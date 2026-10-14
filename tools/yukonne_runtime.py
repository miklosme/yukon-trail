"""Verified Yukon NE selector/import fixups for bounded native instruction harnesses.

Source media stays unchanged. This builds in-memory loaded images, with explicit
synthetic selectors, rather than interpreting raw linked selector-chain words as
real pointers. Unsupported OS fixups remain recorded and are not applied.
"""
import hashlib
import struct
from dataclasses import dataclass
try:
    from .yukonbmp import EXE_SHA256
except ImportError:
    from yukonbmp import EXE_SHA256

@dataclass
class LoadedNE:
    images: dict
    selectors: dict
    imports: dict
    fixups: list
    excluded_os_fixups: list
    segments: dict


def load(executable, selectors=None):
    if hashlib.sha256(executable).hexdigest() != EXE_SHA256:
        raise ValueError('Unsupported executable identity')
    ne = struct.unpack_from('<I', executable, 0x3c)[0]
    count = struct.unpack_from('<H', executable, ne + 0x1c)[0]
    selectors = selectors or {i: i * 0x1000 for i in range(1, count + 1)}
    if set(selectors) != set(range(1, count + 1)):
        raise ValueError('Explicit selector for every source NE segment required')
    table = ne + struct.unpack_from('<H', executable, ne + 0x22)[0]
    shift = struct.unpack_from('<H', executable, ne + 0x32)[0]
    modules_offset = ne + struct.unpack_from('<H', executable, ne + 0x28)[0]
    names = ne + struct.unpack_from('<H', executable, ne + 0x2a)[0]
    module_count = struct.unpack_from('<H', executable, ne + 0x1e)[0]
    modules = {}
    for i in range(1, module_count + 1):
        at = names + struct.unpack_from('<H', executable, modules_offset + 2 * (i - 1))[0]
        modules[i] = executable[at + 1:at + 1 + executable[at]].decode('ascii')
    images, segments, records = {}, {}, []
    for i in range(1, count + 1):
        sector, size, flags, minimum = struct.unpack_from('<4H', executable, table + 8 * (i - 1))
        initialized = sector << shift if sector else None
        size = (size or 65536) if sector else 0
        image = bytearray(65536)
        if initialized is not None:
            image[:size] = executable[initialized:initialized + size]
        images[i] = image
        segments[i] = {'file_offset': initialized, 'initialized_length': size, 'minimum_allocation': minimum, 'flags': flags}
        if flags & 0x100:
            if initialized is None:
                raise ValueError('Uninitialized relocation segment unsupported')
            at = initialized + size
            for j in range(struct.unpack_from('<H', executable, at)[0]):
                records.append((i, struct.unpack_from('<BB3H', executable, at + 2 + 8 * j)))
    imported = sorted({(modules[target], ordinal) for _, (kind, flags, off, target, ordinal) in records if flags & 3 == 1})
    import_offsets = {key: 0x100 + 4 * i for i, key in enumerate(imported)}
    imports = {(0xe800, off): key for key, off in import_offsets.items()}
    fixups, excluded = [], []
    for segment, record in records:
        kind, flags, off, target, value = record
        if flags & 3 == 3:
            excluded.append([segment, *record])
            continue
        if flags & 4 or (kind not in (2, 3, 5)) or (flags & 3 not in (0, 1)):
            raise ValueError(f'Unsupported non-OS fixup {segment}:{record}')
        if flags & 3 == 0:
            if kind != 2 or target not in selectors:
                raise ValueError('Only observed direct segment-selector internal fixups supported')
            replacement = struct.pack('<H', selectors[target])
        else:
            key = (modules[target], value)
            if kind == 3:
                replacement = struct.pack('<HH', import_offsets[key], 0xe800)
            elif kind == 5:
                replacement = struct.pack('<H', import_offsets[key])
            else:
                raise ValueError('Import selector-only fixup unsupported')
        image = images[segment]
        visited = set()
        while off not in (0, 65535):
            if off in visited or off + len(replacement) > len(image):
                raise ValueError('Malformed source relocation chain')
            visited.add(off)
            next_off = struct.unpack_from('<H', image, off)[0]
            before = bytes(image[off:off + len(replacement)])
            image[off:off + len(replacement)] = replacement
            fixups.append({'ne_segment': segment, 'offset': off, 'kind': kind, 'target': [target, value], 'before_hex': before.hex(), 'after_hex': replacement.hex()})
            off = next_off
    return LoadedNE(images, selectors, imports, fixups, excluded, segments)
