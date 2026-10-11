# Supplied image and Archive provenance

Checked: 2026-10-04, from the owner's supplied
[Internet Archive item](https://archive.org/details/YUKONCD). Raw evidence is
preserved under ignored `local/evidence/archive/`; no ISO was downloaded again.

**Observed:** the local `original/iso/YUKONCD.ISO` matches every published
identity field for `YUKONCD.ISO` in the
[item metadata](https://archive.org/metadata/YUKONCD) and
[file-list XML](https://archive.org/download/YUKONCD/YUKONCD_files.xml):

| Check | Local and published value |
| --- | --- |
| Bytes | 370,939,904 |
| MD5 | `b601aede7a8ab3b98d4f619c157a6f35` |
| SHA-1 | `b79512d26f92effcfa8ec93a1264942ace1ad158` |
| CRC32 | `b1d531a5` |

The local SHA-256 remains
`89f8eb97bd7d3afdbabbd05dce10854673eff5c5617825940994aba7a0360ed8`.
Archive publishes no SHA-256 for this file. This establishes a checksum match
to the owner-named item, not completeness of a physical disc or original-game
behavior. The owner's download date remains unknown; the item's added date is
2020-06-25, not a download date.

**Observed:** the JSON and XML list the same eight files: `YUKONCD.ISO`,
`81Rs8Qe9zJL._AC_SL1434_.jpg`, `81Rs8Qe9zJL._AC_SL1434__thumb.jpg`,
`__ia_thumb.jpg`, `YUKONCD_archive.torrent`, `YUKONCD_files.xml`,
`YUKONCD_meta.sqlite`, and `YUKONCD_meta.xml`. The published item lists no
CUE/BIN, separate audio tracks, or Windows installation/guest media.
The torrent is a listed metadata file; its contents were not downloaded or
inspected. This inventory is scoped to this item's current public listing.

**Observed on the disc:** `README.TXT` (SHA-256
`06349946597598f5eb66d1a54d1a44e480b1e56f3c2775c6a4d252577861feb2`)
describes bonus CD audio tracks 2–18 at file offsets `0xa58`–`0x10c5`.
**Unknown:** original track contents, in-game CD audio use, and whether equivalent
music resides in resources. The item listing cannot establish that game music
is missing. See [audio findings](FINDINGS.md#audio-completeness).

## Evidence and reproduction

Python 3.14.5 and curl 8.7.1 were used. Network access was needed only for these
small public metadata files:

```sh
mkdir -p local/evidence/archive
curl --fail --show-error --location --connect-timeout 20 --max-time 60 \
  https://archive.org/metadata/YUKONCD \
  -o local/evidence/archive/YUKONCD.metadata.json
curl --fail --show-error --location --connect-timeout 20 --max-time 60 \
  --dump-header local/evidence/archive/YUKONCD.files.headers.txt \
  https://archive.org/download/YUKONCD/YUKONCD_files.xml \
  -o local/evidence/archive/YUKONCD_files.xml
python3 - <<'PY'
import hashlib, json, pathlib, xml.etree.ElementTree as ET, zlib
root = pathlib.Path('.')
metadata = json.loads((root / 'local/evidence/archive/YUKONCD.metadata.json').read_bytes())
files = metadata['files']
listing = ET.parse(root / 'local/evidence/archive/YUKONCD_files.xml')
assert sorted(f['name'] for f in files) == sorted(
    f.attrib['name'] for f in listing.findall('file'))
published = next(f for f in files if f['name'] == 'YUKONCD.ISO')
iso = root / 'original/iso/YUKONCD.ISO'
checks = {name: hashlib.new(name) for name in ('md5', 'sha1', 'sha256')}
crc = 0
with iso.open('rb') as stream:
    while block := stream.read(4 * 1024 * 1024):
        for digest in checks.values():
            digest.update(block)
        crc = zlib.crc32(block, crc)
assert iso.stat().st_size == int(published['size'])
for name in ('md5', 'sha1'):
    assert checks[name].hexdigest() == published[name], name
assert f'{crc:08x}' == published['crc32']
manifest = json.loads((root / 'docs/source-manifest.json').read_bytes())
expected = next(f for f in manifest['files'] if f['role'] == 'source_disc_image')
assert checks['sha256'].hexdigest() == expected['sha256']
print('Published size/MD5/SHA-1/CRC32 match; recorded SHA-256 unchanged')
PY
```

The retrieved JSON is 2,944 bytes, SHA-256
`5911ecc6da195e06653499c5bed8bbdaa292ddcf8139afdbf219abe45ca4af37`;
XML is 2,414 bytes, SHA-256
`f4df1ef1d09ec18205071dafec72226bd453051ebd4f1097ede2840b94dbf32d`.
`local/evidence/archive/YUKONCD.verification.json` records the comparison.
Live metadata can change; these hashes identify this session's snapshots.
The [versioned manifest](source-manifest.json) retains the essential provenance
even without local snapshots. The ISO was read only.
