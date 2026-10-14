#!/usr/bin/env python3
"""Bounded archive postread normalization; no resource/game semantics inferred."""
from dataclasses import dataclass
import argparse
import hashlib
import json
from pathlib import Path
import struct

try:
    from .yukonbmp import EXE_SHA256
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
except ImportError:
    from yukonbmp import EXE_SHA256
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST


class TransformError(ValueError):
    pass


@dataclass(frozen=True)
class Pattern:
    tag: str
    call_offset: int
    opcodes: tuple[int, ...]


def source_patterns(executable: bytes) -> dict[str, Pattern]:
    """Read only the verified startup registration push sequence NE1:677f..6a25.

    Stack order, literal pushes and caller cleanup are checked explicitly. The
    first PUSH AX is zero on the source branch following the successful open.
    Context pointers are scratch placeholders; pattern/tag literals are original.
    """
    if hashlib.sha256(executable).hexdigest() != EXE_SHA256:
        raise TransformError('unsupported executable identity')
    cursor, stack, patterns = 0x677f, b'', {}
    while cursor < 0x6a25:
        code = executable[0x460+cursor:0x460+cursor+6]
        if code[:2] == b'\x66\x68':
            stack = code[2:6] + stack
            cursor += 6
        elif code[:5] == bytes.fromhex('66ff36f452'):
            stack = struct.pack('<HH', 0, 0x4000) + stack
            cursor += 5
        elif code[0] == 0x68:
            stack = code[1:3] + stack
            cursor += 3
        elif code[0] == 0x50 and cursor == 0x677f:
            stack = b'\0\0' + stack
            cursor += 1
        elif code[:3] == bytes.fromhex('9ae483'):
            if len(stack) < 10 or len(stack) % 2:
                raise TransformError('invalid startup registration stack')
            tag = int.from_bytes(stack[4:8], 'little').to_bytes(4, 'big').decode('ascii')
            opcodes = struct.unpack('<'+'h'*((len(stack)-8)//2), stack[8:])
            if tag in patterns or opcodes[-1] != 0 or 0 in opcodes[:-1]:
                raise TransformError('invalid startup registration pattern')
            patterns[tag] = Pattern(tag, cursor, opcodes)
            cursor += 5
        elif code[:2] == bytes.fromhex('83c4') and code[2] == len(stack):
            stack = b''
            cursor += 3
        else:
            raise TransformError(f'unsupported registration instruction NE1:{cursor:04x}')
    if len(patterns) != 17:
        raise TransformError('registration coverage mismatch')
    return patterns


def transform(payload: bytes, opcodes: tuple[int, ...] | None) -> bytes:
    """Apply checked byte/word operations with bounded reads/skips.

    None means no registered tag, which the original leaves unchanged. The
    source has a single repeat slot; nested repeats are deliberately unsupported.
    Huge segmented-pointer behavior is not emulated by this byte-buffer model.
    """
    if opcodes is None:
        return payload
    if not opcodes or opcodes[-1] != 0:
        raise TransformError('missing pattern terminator')
    output = bytearray(payload)

    def swap(position, size):
        if position < 0 or position + size > len(output):
            raise TransformError(f'transform read outside payload at {position}+{size}')
        output[position:position+size] = output[position:position+size][::-1]

    if opcodes[0] == -7:
        if not output or len(output) % 2:
            raise TransformError('whole-word transform requires positive even length')
        for position in range(0, len(output), 2):
            swap(position, 2)
        return bytes(output)
    cursor, index, loop_index, count_word, steps = 0, 0, None, None, 0
    while index < len(opcodes):
        opcode = opcodes[index]
        if opcode == 0:
            break
        steps += 1
        if steps > 1000000:
            raise TransformError('transform instruction bound exceeded')
        if opcode in (-2, -3, -4):
            size = 4 if opcode == -3 else 2
            swap(cursor, size)
            if opcode == -4:
                if loop_index is not None:
                    raise TransformError('nested repeat slots are unsupported')
                count_word = int.from_bytes(output[cursor:cursor+2], 'little')
                loop_index = index
            cursor += size
        elif opcode == -5:
            if loop_index is None:
                raise TransformError('repeat end without count')
            count_word = (count_word - 1) & 65535
            if 0 < count_word < 32768:
                index = loop_index
            else:
                loop_index = None
        elif opcode in (-1, -6):
            cursor += 1 if opcode == -1 else 256
        elif opcode == -8:
            index += 1
            if index >= len(opcodes):
                raise TransformError('signed skip operand missing')
            cursor += opcodes[index]
        else:
            raise TransformError(f'unsupported transform opcode {opcode}')
        if not 0 <= cursor <= len(output):
            raise TransformError('transform skip outside payload')
        if cursor == len(output):
            break  # Original checks end pointer after each operation.
        index += 1
    return bytes(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('executable', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--key', action='append', required=True)
    args = parser.parse_args()
    patterns = source_patterns(args.executable.read_bytes())
    if args.output.exists():
        parser.error('output must be a fresh directory')
    exports = {}
    with args.archive.open('rb') as source:
        archive_hash = verify_source(source, DEFAULT_SOURCE_MANIFEST)
        index = read_index(source).by_key()
        for key in sorted(set(args.key)):
            if key not in index:
                raise TransformError(f'missing resource {key}')
            resource = index[key]
            pattern = patterns.get(resource.tag)
            source.seek(resource.offset)
            raw = source.read(resource.length)
            normalized = transform(raw, pattern.opcodes if pattern else None)
            exports[key] = (resource, pattern, raw, normalized)
    args.output.mkdir(parents=True)
    records = {}
    for key, (resource, pattern, raw, normalized) in exports.items():
        name = f'{resource.tag}-{resource.resource_id}-normalized.bin'
        (args.output/name).write_bytes(normalized)
        records[key] = dict(offset=resource.offset, length=resource.length,
                            raw_sha256=hashlib.sha256(raw).hexdigest(),
                            normalized_sha256=hashlib.sha256(normalized).hexdigest(), path=name,
                            opcodes=list(pattern.opcodes) if pattern else None,
                            registration_ne=f'0001:{pattern.call_offset:04x}' if pattern else None)
    report = dict(archive_sha256=archive_hash, executable_sha256=EXE_SHA256, resources=records,
                  scope='Postread byte normalization only; no dialogue, scene or opcode semantics')
    (args.output/'manifest.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(resources=len(records),output=str(args.output))))


if __name__ == '__main__':
    main()
