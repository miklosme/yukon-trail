# Classic Macintosh source inventory

Inspected 2026-10-04. This is a read-only catalog/fork inventory, not a Mac game installation or behavioral comparison. No volume was mounted and no forks were extracted.

## Source identity and method

**Observed source:** `original/iso/YUKONCD.ISO`, 370,939,904 bytes, SHA-256 `89f8eb97bd7d3afdbabbd05dce10854673eff5c5617825940994aba7a0360ed8`.

[The inventory tool](../tools/hfs_inventory.py) opens the image with `rb` and a read-only memory map. It interprets classic HFS structures using [Apple's published format declarations](https://github.com/apple-oss-distributions/hfs/blob/main/core/hfs_format.h): the master directory block, catalog keys/records, inline extent descriptors, and B-tree node/header records. Source offsets below are absolute ISO byte offsets; allocation block numbers are relative to the HFS allocation area.

Reproduce from the repository root with Python 3.10 or newer; verified here with Python 3.14.5:

```sh
python3 -m unittest discover -s tests -p test_hfs_inventory.py -v
python3 tools/hfs_inventory.py original/iso/YUKONCD.ISO \
  --expect-sha256 89f8eb97bd7d3afdbabbd05dce10854673eff5c5617825940994aba7a0360ed8
```

The second command emits deterministic JSON to stdout, including source/fork hashes, original name bytes, raw catalog values, paths as components, CNIDs, and every inline extent. For a durable local artifact:

```sh
mkdir -p local/evidence
python3 tools/hfs_inventory.py original/iso/YUKONCD.ISO \
  --expect-sha256 89f8eb97bd7d3afdbabbd05dce10854673eff5c5617825940994aba7a0360ed8 \
  > local/evidence/mac-source-inventory.json
```

An unsupported/malformed input exits nonzero without emitting a partial inventory. Check that exit status before using a redirected file. Keep this generated inventory local; it includes catalog metadata for unrelated bundled products.

## Observed geometry and catalog

| Item | Source location / value |
| --- | --- |
| Apple partition map | Two entries at `0x200` and `0x400`, both `PM` signatures |
| HFS partition | Map entry 2; start block `0x5b142` = 373,058; byte offset `0xb628400`; length `0x55810` = 350,224 blocks of 512 bytes |
| HFS partition name/type | `Toast 3.5 PPC HFS Optimizer` / `Apple_HFS` |
| Master directory block | `0xb628800`; signature `BD`; volume `Yukon Trail` |
| Allocation area | `0xb62a000`; 43,776 allocation blocks of 4,096 bytes |
| Extents-overflow file | Allocation extent `(0, 1)`; 4,096 bytes at `0xb62a000`; header advertises zero leaf records |
| Catalog file | Allocation extent `(1, 11)`; 45,056 bytes at `0xb62b000` |
| Catalog SHA-256 | `5f82e6de2f1ad877d6623f8aea875600f64344b0b9b1a35d933662b25bac93ab` |
| Catalog header | 512-byte nodes; 88 total nodes; depth 3; root node 2; first/last leaves 9/64 |
| Traversed leaves | 56 linked nodes; all 219 advertised leaf records accounted for |
| Catalog record counts | 170 files; 24 folders including root; 24 folder threads; 1 file thread |
| Resource forks | 99 nonempty forks, totaling 55,876,533 logical bytes |

MDB file/directory counts agree with the traversed catalog (the MDB's 23-directory count excludes the root). All catalog/fork extents fit the partition, and all recorded physical fork sizes equal their inline allocation capacity. No extents-overflow lookup was needed. The observed Toast keys count a zero padding byte in `keyLength` for even-length names; the reader accepts that representation and an unpadded key length.

Root catalog entries include `Installer`, `The Yukon Trail CD`, and `YUKONRES`. Other folders include `Yukon literature`, `MECC Demos`, `AOL`, and `Ereg`; those are separate content. Some original names include carriage returns (`Icon\r`, `OpenFolderListDF\r`), so preserving raw names/CNIDs matters before choosing output filenames.

## Main game forks and archive equivalence

These logical-byte hashes were checked both through the inventory reader and by a separate `seek`/chunked-hash calculation using the absolute offsets below.

| Catalog file | CNID | Fork | Inline allocation extent | Absolute source offset | Logical length |
| --- | ---: | --- | --- | --- | ---: |
| `Yukon Trail:The Yukon Trail CD` | 175 | data | `(624, 97)` | `0xb89a000` | 393,347 |
| Same file | 175 | resource | `(356, 268)` | `0xb78e000` | 1,097,445 |
| `Yukon Trail:YUKONRES` | 185 | data | `(721, 21463)` | `0xb8fb000` | 87,911,322 |
| Same file | 185 | resource | empty | — | 0 |

- Main application data-fork SHA-256: `6dee34305322049f87473bf52fc6cdf0fab5f2c0dfcfd1c0b57738f41f7e0f77`.
- Main application resource-fork SHA-256: `f23210212907d794fb5e0c2397c2d24f30d36c3a8db12168435b17579d621886`.
- Mac `YUKONRES` data-fork SHA-256: `438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`.

**Observed:** the Mac `YUKONRES` logical data fork matches the Windows archive's size and SHA-256 in [the source manifest](source-manifest.json). This establishes identical archive bytes on this disc. It does not establish identical executables, platform rendering, resource consumers, or gameplay behavior. The main Mac application's Finder type/creator bytes are `APPL` / `YUTR`; its executable format and resources remain unexamined.

Independent hash reproduction:

```sh
python3 - <<'PY'
from hashlib import sha256
with open('original/iso/YUKONCD.ISO', 'rb') as source:
    source.seek(0xb8fb000)
    remaining = 87911322
    result = sha256()
    while remaining:
        block = source.read(min(remaining, 1024 * 1024))
        if not block:
            raise ValueError('truncated source')
        result.update(block)
        remaining -= len(block)
print(result.hexdigest())
PY
```

## Fork-preserving extraction approach and limits

**Recommended next extraction:** extend the bounded reader to write each selected file's data and resource forks verbatim as separate CNID-named files under `original/extracted/mac/`, accompanied by the inventory metadata and separate output hashes. Preserve raw catalog values, original name bytes, Finder fields, dates, folder hierarchy, and the canonical ISO. Verify each output against its recorded logical-fork hash. Separate files and metadata make both forks inspectable without depending on host filesystem extended attributes or silently dropping an empty/nonempty fork. This extraction extension has not been implemented or tested.

An alternative is an established fork-preserving container such as MacBinary via [hfsutils](https://www.mars.org/home/rob/proj/hfs/), which supports partitioned HFS images and MacBinary transfers. It would need a verified read-only configuration, an isolated tool state location, and comparisons against this inventory before use. `hmount`, `hls`, and `hcopy` were absent from the local command path; no software was installed. Available tools were macOS `hdiutil`/`diskutil`, `bsdtar` 3.5.3, and Python. No `7z`, `unar`, `machfs`, or `pytsk3` was available. The earlier `hdiutil imageinfo` failure in [FINDINGS.md](FINDINGS.md) remains unresolved; mounting is unnecessary for this inventory.

**Verified scope:** 22 synthetic tests cover independent data/resource content, multiple inline extents, empty forks, exact logical lengths, control characters and padding in names, source identity, truncation, unsupported signatures/overflow, bad bounds/counts/links, overlapping inline extents, duplicate CNIDs, and invalid parents. The actual ISO passes the bounded inventory and hashes above. The reader supports exactly one classic HFS partition in a 512-byte Apple partition map, 512-byte B-tree nodes, an empty overflow tree, and inline extent capacity matching physical fork sizes; other structures fail explicitly.

**Unknown/unverified:** allocation bitmap consistency and cross-file extent overlaps, catalog index-node ordering/search behavior, thread-to-record consistency, alternate MDB, MacBinary generation/import, restoration into a classic Mac filesystem, executable architecture, and Mac original-game execution. The tool is an inventory for this subset, not a general HFS filesystem driver.
