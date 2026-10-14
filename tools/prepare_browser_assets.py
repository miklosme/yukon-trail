#!/usr/bin/env python3
"""Prepare explicit source-verified indexed CBMP frames/font for the local browser.

Lossless indices remain separate from runtime display normalization. No guessed
scene field meanings, opacity or original UI layout are generated.
"""
import argparse
from dataclasses import asdict
import io
import wave
import hashlib
import json
from pathlib import Path
try:
    from .yukonbmp import decode, source_palette, EXE_SHA256
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from .inspect_yukon_font import inspect as inspect_font
    from .yukonjournal import source_vocabulary, linda_text_from_raw_cstr505
    from .yukontransform import source_patterns, transform
    from .yukontree import decode_normalized
    from .yukonsnd import decode as decode_sound
    from .prepare_journal_status import source_data as status_source_data
    from .prepare_seattle_population import source_data as population_source_data
    from .prepare_cached_frames import source_data as cache_source_data
except ImportError:
    from yukonbmp import decode, source_palette, EXE_SHA256
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from inspect_yukon_font import inspect as inspect_font
    from yukonjournal import source_vocabulary, linda_text_from_raw_cstr505
    from yukontransform import source_patterns, transform
    from yukontree import decode_normalized
    from yukonsnd import decode as decode_sound
    from prepare_journal_status import source_data as status_source_data
    from prepare_seattle_population import source_data as population_source_data
    from prepare_cached_frames import source_data as cache_source_data


def prepare(archive, executable, font, output, bitmap_ids, system_zero, tree_ids=(), sound_ids=(), journal=False, sound_evidence=None, journal_status=False, seattle_population=False):
    if output.exists():
        raise FileExistsError('Choose a fresh asset directory; existing assets are not replaced')
    if not bitmap_ids or any(not isinstance(i, int) or i < 0 or i > 65535 for i in bitmap_ids):
        raise ValueError('Explicit CBMP resource IDs required')
    if len(system_zero) != 3 or any(not 0 <= i <= 255 for i in system_zero):
        raise ValueError('Explicit reference palette0 RGB required')
    exe_bytes = executable.read_bytes()
    original_palette = source_palette(exe_bytes)
    palette = bytes(system_zero) + original_palette[3:]
    font_metadata = inspect_font(font)
    prepared = {'source-palette.rgb': original_palette, 'display-palette.rgb': palette,
                'YUF_____.TTF': font.read_bytes()}
    with archive.open('rb') as source:
        archive_hash = verify_source(source, DEFAULT_SOURCE_MANIFEST)
        if sound_evidence is not None and (
            sound_evidence.get('archive_sha256') != archive_hash or
            sound_evidence.get('executable_sha256') != EXE_SHA256):
            raise ValueError('Native sound evidence source identity mismatch')
        index = read_index(source).by_key()
        resources = {}
        for resource_id in sorted(set(bitmap_ids)):
            key = f'CBMP:{resource_id}'
            if key not in index:
                raise ValueError(f'Missing selected resource {key}')
            record = index[key]
            source.seek(record.offset)
            raw = source.read(record.length)
            frames = []
            for number, frame in enumerate(decode(raw)):
                name = f'CBMP-{resource_id}-frame-{number}.idx'
                prepared[name] = frame.pixels
                frames.append({'frame': number, 'width': frame.width, 'height': frame.height,
                               'payload_offset': frame.offset, 'compressed_length': frame.length,
                               'indices': name, 'indices_sha256': hashlib.sha256(frame.pixels).hexdigest()})
            resources[key] = {'offset': record.offset, 'length': record.length,
                              'raw_sha256': hashlib.sha256(raw).hexdigest(), 'frames': frames}
        trees = {}
        sounds = {}
        patterns = source_patterns(exe_bytes)
        for resource_id in sorted(set(tree_ids)):
            key = f'TREE:{resource_id}'
            record = index[key]
            source.seek(record.offset)
            raw = source.read(record.length)
            normalized = transform(raw, patterns['TREE'].opcodes)
            tree = decode_normalized(normalized)
            def textual(value):
                if isinstance(value, bytes):
                    return {'latin1': value.decode('latin1'), 'bytes_hex': value.hex()}
                if isinstance(value, dict):
                    return {k: textual(v) for k, v in value.items()}
                if isinstance(value, (tuple, list)):
                    return [textual(v) for v in value]
                return value
            data = {'schema': 'source-tree-graph-v1', 'resource': key,
                    'graph': textual(asdict(tree)), 'provenance': {
                        'offset': record.offset, 'length': record.length,
                        'raw_sha256': hashlib.sha256(raw).hexdigest(),
                        'normalized_sha256': hashlib.sha256(normalized).hexdigest(),
                        'scope': 'Original recursive graph; unknown field semantics retained; no condition/action defaults'}}
            name = f'TREE-{resource_id}.json'
            prepared[name] = (json.dumps(data, indent=2, sort_keys=True) + '\n').encode()
            trees[key] = {'file': name, 'sha256': hashlib.sha256(prepared[name]).hexdigest()}
        for resource_id in sorted(set(sound_ids)):
            key = f'PSND:{resource_id}'
            record = index[key]
            source.seek(record.offset)
            raw = source.read(record.length)
            try:
                sound = decode_sound(raw)
            except ValueError as error:
                raise ValueError(f'{key} at0x{record.offset:x}: {error}') from error
            if sound_evidence is not None:
                expected = sound_evidence.get('sounds', {}).get(key)
                if expected is None or expected.get('raw_sha256') != hashlib.sha256(raw).hexdigest() or \
                   expected.get('offset') != record.offset or expected.get('sample_bytes') != len(sound.samples) or \
                   expected.get('native_pcm_sha256') != hashlib.sha256(sound.samples).hexdigest():
                    raise ValueError(f'Original native sound oracle mismatch: {key}')
            target = io.BytesIO()
            with wave.open(target, 'wb') as wav:
                wav.setnchannels(sound.channels)
                wav.setsampwidth(sound.sample_bits // 8)
                wav.setframerate(sound.sample_rate)
                wav.writeframes(sound.samples)
            name = f'PSND-{resource_id}.wav'
            prepared[name] = target.getvalue()
            sounds[key] = {'file': name, 'sha256': hashlib.sha256(prepared[name]).hexdigest(),
                           'offset': record.offset, 'length': record.length,
                           'raw_sha256': hashlib.sha256(raw).hexdigest(),
                           'samples': len(sound.samples), 'rate': sound.sample_rate,
                           'channels':sound.channels,'sample_bits':sound.sample_bits,
                           'pcm_sha256':hashlib.sha256(sound.samples).hexdigest(),
                           'integration_order':sound.order,'declared_bits':sound.packed_bits,
                           'consumed_bits':sound.consumed_bits,
                           'terminal_unused_bits':sound.terminal_unused_bits}
        journal_data = None
        if journal:
            vocabulary = source_vocabulary(exe_bytes)
            record = index['CSTR:505']
            source.seek(record.offset); raw = source.read(record.length)
            strings = {k: ([v.decode('latin1') for v in value] if isinstance(value, tuple)
                           else value.decode('latin1')) for k, value in asdict(vocabulary).items()}
            journal_data = {'schema': 'selected-linda-journal-v1', 'vocabulary': strings,
                            'linda_text': linda_text_from_raw_cstr505(raw).decode('latin1')}
            record = index['CSTR:504']
            source.seek(record.offset); raw = source.read(record.length)
            if raw[:2] != bytes([0,3]) or len(raw[2:].split(b'\0')) != 4:
                raise ValueError('Unsupported journal header resource')
            journal_data['header_strings'] = [part.decode('latin1') for part in raw[2:].split(b'\0')[:-1]]
            journal_data['header_provenance'] = {'resource':'CSTR:504', 'offset':record.offset,
                                                'length':record.length,'sha256':hashlib.sha256(raw).hexdigest()}
            # Observed initial-entry fragments; offsets remain explicit provenance.
            fragments = {}
            for label, offset in [('arrival_prefix', 0x504b9), ('have_prefix', 0x50526),
                                  ('food_to_cash', 0x50553), ('cash_suffix', 0x5056c)]:
                if exe_bytes[offset - 1] != 0:
                    raise ValueError(f'Initial journal fragment does not begin at a source string boundary:0x{offset:x}')
                fragment = exe_bytes[offset:offset + 96].split(b'\0')[0]
                fragments[label] = {'text': fragment.decode('latin1'), 'executable_file_offset': offset}
            journal_data['initial_fragments'] = fragments
            name = 'journal.json'
            prepared[name] = (json.dumps(journal_data, indent=2, sort_keys=True) + '\n').encode()
    if journal_status:
        prepared['journal-status.json'] = (json.dumps(status_source_data(exe_bytes),indent=2,sort_keys=True)+'\n').encode()
    if seattle_population:
        population=population_source_data(archive,executable)
        missing={f'CBMP:{id}'for id in population['bitmaps']}-resources.keys()
        if missing:raise ValueError(f'Select all required population bitmaps: {sorted(missing)}')
        prepared['seattle-population.json']=(json.dumps(population,indent=2,sort_keys=True)+'\n').encode()
        cache,cache_files=cache_source_data(archive,executable,ids=[int(i)for i in population['bitmaps']])
        prepared.update(cache_files)
        prepared['cached-frames.json']=(json.dumps(cache,indent=2,sort_keys=True)+'\n').encode()
        navigation={}
        with archive.open('rb') as source:
            for scene_id,scene in population['scenes'].items():
                hotspot_id=scene['scne_words'][2];record=index[f'HSPT:{hotspot_id}']
                source.seek(record.offset);raw=source.read(record.length)
                normalized=transform(raw,patterns['HSPT'].opcodes)
                name=f'HSPT-{hotspot_id}-normalized.bin';prepared[name]=normalized
                navigation[scene_id]={'hotspot_id':hotspot_id,'file':name,
                    'offset':record.offset,'length':record.length,
                    'raw_sha256':hashlib.sha256(raw).hexdigest(),
                    'sha256':hashlib.sha256(normalized).hexdigest()}

    manifest = {'schema': 'yukon-indexed-assets-v1', 'archive_sha256': archive_hash,
                'executable_sha256': EXE_SHA256, 'resources': resources, 'trees': trees, 'sounds': sounds,
                'journal': {'file':'journal.json','sha256':hashlib.sha256(prepared['journal.json']).hexdigest()} if journal else None,
                'journal_status': {'file':'journal-status.json','sha256':hashlib.sha256(prepared['journal-status.json']).hexdigest()} if journal_status else None,
                'seattle_population': {'file':'seattle-population.json','sha256':hashlib.sha256(prepared['seattle-population.json']).hexdigest()} if seattle_population else None,
                'cached_frames': {'file':'cached-frames.json','sha256':hashlib.sha256(prepared['cached-frames.json']).hexdigest()} if seattle_population else None,
                'seattle_navigation': navigation if seattle_population else None,
                'source_palette': {'file': 'source-palette.rgb', 'executable_offset': 0x618e0,
                                   'sha256': hashlib.sha256(original_palette).hexdigest()},
                'display_palette': {'file': 'display-palette.rgb', 'supplied_zero_rgb': list(system_zero),
                                    'sha256': hashlib.sha256(palette).hexdigest(),
                                    'scope': 'Explicit inferred reference palette0; remaining RGB from source. Runtime must apply recovered display-index normalization; no universal alpha.'},
                'font': {'file': 'YUF_____.TTF', 'sha256': font_metadata['sha256'],
                         'scope': 'Original font unchanged; browser/native rasterization remains unverified'}}
    # Decode and verify all inputs before creating any output.
    output.mkdir(parents=True)
    for name, data in prepared.items():
        (output / name).write_bytes(data)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'executable', 'font', 'output'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--bitmap', type=int, action='append', required=True)
    parser.add_argument('--system-palette-zero-rgb', required=True)
    parser.add_argument('--tree', type=int, action='append', default=[])
    parser.add_argument('--sound', type=int, action='append', default=[])
    parser.add_argument('--journal', action='store_true')
    parser.add_argument('--journal-status',action='store_true')
    parser.add_argument('--seattle-population',action='store_true')
    parser.add_argument('--sound-evidence',type=Path,help='Optional independent original PCM evidence; mismatches fail before output')
    args = parser.parse_args()
    try:
        zero = tuple(int(v) for v in args.system_palette_zero_rgb.split(','))
    except ValueError:
        parser.error('Palette0 requires three integers0..255')
    result = prepare(args.archive, args.executable, args.font, args.output, args.bitmap, zero, args.tree, args.sound, args.journal, json.loads(args.sound_evidence.read_text()) if args.sound_evidence else None, args.journal_status,args.seattle_population)
    print(json.dumps({'output': str(args.output), 'resources': len(result['resources']),
                      'frames': sum(len(r['frames']) for r in result['resources'].values())}))
