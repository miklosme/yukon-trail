# YUKONRES index, edition 1.1

This specification describes the index of the supplied Windows archive, not its
payload formats. Source: `original/extracted/windows/YUKONRES`, 87,911,322 bytes,
SHA-256 `438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`.
All offsets below are file offsets. Investigation date: 2026-10-04.

## Observed layout

Index integers are unsigned and big-endian. Payload layouts must be checked
per type; selected CBMP numeric headers are little-endian as documented in
[CBMP.md](CBMP.md).

| Offset | Size | Field |
| --- | ---: | --- |
| `0x04` | 4 | `MECC` signature |
| `0x54` | 2 | Type-group count, 21 |
| `0x56` | 2 | Resource count, 2,522 |
| `0x58` | 21 × 8 | Type groups |
| `0x100` | 2,522 × 14 | Resource records |
| `0x8aec` | — | End of index, exclusive; first payload starts here |

Each group contains a four-byte ASCII tag, a u16 record count, and a u16 first
record index. Each record contains a four-byte tag, u16 resource ID, u32 payload
length, and u32 absolute payload offset. Resource IDs are preserved as integers;
their meaning and any relationship between different types remain unknown.

**Observed:** groups are contiguous in index order and cover every record exactly
once. Group tags are unique; every group slice contains only that group's tag.
All `(type, ID)` pairs are unique. All payloads lie within the file, after the
index. Positive-length payload ranges do not overlap. The final payload ends at
`0x53d6b9a`, exactly the archive size. Gaps between some payloads are present;
their contents and purpose are not interpreted.

**Observed:** `TREE:39`, index entry at `0x7058`, has length zero and offset
`0x52a96df`. A zero-length record is therefore valid in this edition. Its meaning
is unknown; it must not be discarded or assigned invented content.

**Observed static consumer confirmation:** NE `0001:73fa` / Ghidra `1000:73fa`
reads `0x58` bytes, then group-count × 8 and record-count × 14 sequentially,
swapping the numeric fields described above. This establishes the immediate
table relation (`0x58 + 21 × 8 = 0x100`) for this path, matching the archive
bytes. The native lookup at NE `0001:75fe` / Ghidra `1000:75fe` matches all 2,522
physical index ordinals and 43 absent keys in a static consistency check.
Groups' IDs are ordered for that search. Counts/bounds use signed 16-bit
operations; ID comparisons use unsigned words. The CLI accepts only the
verified source edition. Other editions need fresh evidence; see
[consumer evidence](../ARCHIVE-CONSUMERS.md).

## Reader contract

`tools/yukonres.py` uses Python's standard library. It validates the complete
index before producing output: signature, table bounds, nonzero table counts,
ASCII tags, duplicate groups/keys, contiguous group coverage, group membership,
payload bounds, and positive-length payload overlaps. An overlap is explicitly
unsupported by this reader, rather than proof that every MECC archive forbids it.
Python integer arithmetic does not wrap when computing range ends.

The command-line tool checks source size and SHA-256 against
`docs/source-manifest.json`; unknown input identity fails before any output is
created. Structural functions are independently usable on synthetic fixtures.
No payload decoder or opcode interpreter is included. Unknown resource types
are inventory entries, not inferred behavior.

The deterministic JSON manifest is keyed first by type, then by decimal ID. It
preserves the source identity, index entry offset, payload offset and length,
and hashes of explicitly exported raw payloads. Output files are never
overwritten. Raw exports retain their original bytes with a `.bin` extension.

```sh
python3 tools/yukonres.py original/extracted/windows/YUKONRES \
  --output-dir generated/yukonres-index \
  --extract CBMP:1 --extract PSND:1
python3 -m unittest discover -s tests -v
```

For another run use a fresh output directory. Outputs contain original content
and belong in ignored local directories. The recorded sample expectations come
from the earlier independent inspection in `docs/FINDINGS.md`:

| Key | Offset | Length |
| --- | --- | ---: |
| `CBMP:1` | `0x74dd6` | 1,842 |
| `PSND:1` | `0xbe2a4d` | 45,300 |
| `CSTR:500` | `0xbdfd55` | 2,302 |
| `SCRP:1000` | `0x51be0cd` | 164 |

## Actual local verification

On 2026-10-04, Python 3.14.5 validated all 2,522 entries and 21 groups.
Twenty-three synthetic tests passed, covering handwritten valid bytes,
truncation at every byte, count/group/key errors, bad tags, bounds/overlaps,
u32 range arithmetic, zero-length records, source identity, deterministic
output, and overwrite refusal.

The actual export command additionally requested `CSTR:500`, `SCRP:1000`, and
`TREE:39`. Each export was compared byte for byte against a separate direct read
at the offsets recorded above (plus `TREE:39` at `0x52a96df`, length 0).
Repeated exports with reversed request order produced identical manifests.
`generated/yukonres-index/manifest.json` SHA-256:
`d98715323b98c2cec6de7c5b305baa814ceb5f78fd861c1400019e6c754af3e7`.

| Raw export | SHA-256 |
| --- | --- |
| `CBMP:1` | `f2cccca25cfb50c6ac43e951c5bf9d91b9008ca4b84bc0071ef22f29db95d55c` |
| `PSND:1` | `a671dfae45ada8f46ea6a9d8ce0042d53234106ec6c479e60590ca8f55b1fa40` |
| `CSTR:500` | `87e2961330e674dc064abaa70e4ed30000e3d7b34695a7a6693bc676c6cacf92` |
| `SCRP:1000` | `2be6618a1ad0dd333743087eaa15dac77542d94478d6811d6a9d1a5550d720ed` |
| `TREE:39` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

These checks establish index recovery and byte-preserving export only. Image,
sound, script, and gameplay semantics still require tracing executable consumers
and comparison with the running original.
