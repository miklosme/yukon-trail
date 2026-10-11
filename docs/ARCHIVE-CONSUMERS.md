# Windows archive consumer evidence

Checked 2026-10-04 with Ghidra 12.1.4 and the project-local JDK documented in
[ANALYSIS.md](ANALYSIS.md). **Observed:** the executable contains archive opening,
header/index loading, type/ID lookup, record-length, record-file-slice, and
record-read paths consistent with the independently inventoried archive.
These archive findings are static evidence. The original now runs through one
ending; selected CBMP integer decoding and native border comparison are checked
in [formats/CBMP.md](formats/CBMP.md). Selected sequential PSND decoding and
playback parameters are checked against original code in
[formats/PSND.md](formats/PSND.md); live sound mapping and gameplay-rule fidelity
remain unverified.

## Source and addresses

All executable findings refer to `original/extracted/windows/YUKON.EXE`, SHA-256
`9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`.
Archive consistency checks refer to `original/extracted/windows/YUKONRES`, SHA-256
`438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`.
The active saved program remains `/YUKON.EXE` in `local/ghidra/YukonTrail.gpr`.

| Supported saved name | Original NE entry | Ghidra entry | Source file offset |
| --- | --- | --- | --- |
| `YukonArchive_Initialize` | `0001:673a` | `1000:673a` | `0x6b9a` |
| `YukonArchive_OpenContext` | `0001:722c` | `1000:722c` | `0x768c` |
| `YukonArchive_ReadHeaderAndIndex` | `0001:73fa` | `1000:73fa` | `0x785a` |
| `YukonArchive_FindRecordIndex` | `0001:75fe` | `1000:75fe` | `0x7a5e` |
| `YukonArchive_ReadRecord` | `0001:7818` | `1000:7818` | `0x7c78` |
| `YukonArchive_GetRecordLength` | `0001:7c88` | `1000:7c88` | `0x80e8` |
| `YukonArchive_GetRecordFileSlice` | `0001:7dd2` | `1000:7dd2` | `0x8232` |
| `YukonArchive_OpenFileWithFallback` | `0001:8278` | `1000:8278` | `0x86d8` |
| `ByteSwap16_InPlace` | `0006:60ae` | `1028:60ae` | `0x4b06e` |
| `ByteSwap32_InPlace` | `0006:60c2` | `1028:60c2` | `0x4b082` |
| `PSND_ConsumerLead` | `0003:e1ee` | `1010:e1ee` | `0x2bfce` |

These names describe checked code operations. No guessed parameter signatures
were installed. Stack layouts below come from `LES`, stack accesses, callers,
and `RETF` cleanup, independently of the default decompiler signature.

## Opening and index loading

**Observed:** NE `0001:673a` allocates `0x70c` bytes, then at `6753–6761` pushes
mode `1`, `DS:020d`, `DS:0204`, and the allocated far pair before calling
`0001:722c`. The original Data13 bytes at file `0x4f624` and `0x4f62d` are
`Resource\0` and `YUKONRES\0`. The far return is saved at Data13 offsets
`52f4/52f6` (Ghidra `1060:52f4/52f6`). The header's auto-data segment is NE
`000d`; Ghidra's DS-based references use its Data13 mapping. **Unknown:** actual
runtime DS and these pointers have not been inspected in a running guest. The
observed `PUSH DS` is stronger evidence than the previously absent exact string
xrefs, but does not replace dynamic validation.

`0001:722c` uses `BP+06` for the context far pair, `+0a` for directory, `+0e`
for filename, and `+12` for mode; it returns with `RETF 0x0e`. The code copies
strings, appends a backslash when required, and calls `0001:8278`. That wrapper
passes the far filename at context `+00` and mode zero to `_LOPEN` (Ghidra thunk
`11c8:0060`). It has drive and dialog retries; the complete retry behavior is
not yet recovered. Mode `1` also allows separate-file resource fallbacks.

`0001:73fa` receives one context far pair and returns with `RETF 4`. Its file
handle is the context word at `+12`. The three `_HREAD` calls (Ghidra thunk
`11c8:0098`) establish the following operations:

| NE call | Read size | Destination / retained pointer |
| --- | --- | --- |
| `0001:7419` | `0x58` | inline header at context `+16` |
| `0001:74d5` | type-group count × `8` | far group table at context `+72/+74` |
| `0001:757a` | record count × `14` | far record table at context `+76/+78` |

The inline header count words at context `+6a/+6c` equal header offsets
`+54/+56`. The 16-bit helper swaps header words `+00,+02,+54,+56`; it then swaps
group words `+04,+06` and record word `+04`. The 32-bit helper swaps record
dwords `+06,+0a`. Group and record tags remain four unswapped bytes. This agrees
with [the archive index specification](formats/YUKONRES.md); it does not imply
that all payload fields share that byte order. The meaning of the initial two
header words remains unknown.

**Observed width/signedness:** allocation-size arithmetic here is 16-bit, then
stored with a zero high word for `_HREAD`. Counts and loop bounds use signed
16-bit comparisons (`JLE/JG`). Read-length comparisons use signed high words and
unsigned low words. These operations are safe for the inspected 21 groups and
2,522 records; this is not a claim that the original safely handles malformed
or arbitrarily large archives.

## Type/ID lookup and record reads

`0001:75fe` reads a context far pair at `BP+06`, resource ID word at `+0a`, and
tag dword at `+0c`; `RETF 0x0a` confirms ten bytes of explicit arguments. It
searches 8-byte group rows linearly for the raw tag, then uses the group's count
at `+04` and first record index at `+06` to search 14-byte record rows. IDs are
read at row `+04`, compared as unsigned words (`CMP` at `76a1`, `JBE` at `76a7`).
Bounds/midpoint arithmetic uses signed 16-bit comparisons and division. It
returns the row index in AX or `0xffff` when the key is absent.

Callers supply a logical numeric tag such as `0x43424d50` (`CBMP`) and byteswap
it first. The lookup compares that swapped integer to the untouched tag bytes
as loaded little-endian. It does not reverse the archive tag bytes in memory.

**Static verification:** `tools/ghidra/verify_lookup_trace.py` mirrors the checked
branch/arithmetic sequence for this exact source's bounded counts. It compares
every result with an expected ordinal obtained by directly enumerating the
physical archive index, without importing `tools/yukonres.py`. All **2,522
present keys** return the expected ordinal, and **43 absent keys** (unknown tag
plus below/above each group's ID range) return `-1`; zero mismatches. This checks
consistency between executable-derived search and source data. It is not an
original-versus-port runtime comparison.

| Independent source key | Physical row | Payload offset | Length |
| --- | ---: | --- | ---: |
| `CBMP:1` | 334 | `0x74dd6` | 1,842 |
| `PSND:1` | 893 | `0xbe2a4d` | 45,300 |
| `TREE:39` | 2,036 | `0x52a96df` | 0 |

`0001:7818` accepts context far pair (`BP+06`), destination far pair (`+0a`),
ID word (`+0e`), logical tag dword (`+10`), and returns with `RETF 0x0e`. After
the separate-file branch, its archive path swaps the tag, calls lookup at
`788f`, reads entry offset dword `+0a` at `78ba`, and passes it to `_LLSEEK`
with origin zero at `78d9` (Ghidra thunk `11c8:005c`). It passes entry length
dword `+06` to `_HREAD` at `791c`. The postread call to `0001:8462` searches
a startup-registered tag/pattern table, described below. CBMP and PSND are
absent from those registrations; other types may be transformed. The length
helper `0001:7c88` returns entry `+06` in DX:AX.

### Postread registry scope

**Observed:** NE `0001:8462` / Ghidra `1000:8462`, source file `0x88c2`,
takes context far (`BP+06`), length dword (`+0a`), buffer far (`+0e`), and
logical tag dword (`+12`); `RETF0x10`. It searches context word count `+70a`
and registry rows starting `+7a`, stride `0x54`. Missing tags return without
changing the buffer. Matching rows supply word opcodes; byte-swap16/32 cases
are present, but the full pattern interpreter is not recovered.

Registration NE `0001:83e4` / Ghidra `1000:83e4`, file `0x8844`, has 17
direct call references from startup `0001:673a`, at offsets `6794,67bc,67e1,
6812,6849,6880,68d8,6912,6958,6971,698a,69a3,69bc,69d5,69ee,6a07,6a20`.
Their tags are `CATS, AMSN, SCNE, HSPT, PRRS, SCRP, TRSP, TREE, CONV,
ASEQ, ACEL, WRLD, FNTL, CSTR, FMAP, SMAP, CMIN`. Neither CBMP nor PSND is
registered by this path. This supports using their unchanged raw payloads;
runtime DS contents and other initialization paths were not observed. Do not
generalize unchanged bytes to other types. The missing switch-case disassembly
region `850e–859d` and raw jump table at `85ae` still need work for those types.

`0001:7dd2` accepts context (`BP+06`), far output pointers for length (`+0a`),
offset (`+0e`), and handle (`+12`), followed by ID (`+16`) and logical tag
(`+18`); `RETF 0x16` confirms 22 argument bytes. The archive branch writes the
context file handle and entry dwords `+0a/+06` to those outputs, returning AX
`1`. The separate-file branch can return offset zero and the individual file's
length. Ownership/lifetime of the returned handle is not yet traced completely.

## Bounded CBMP and PSND consumer leads

**Observed CBMP path:** NE `0003:5d50` (Ghidra `1010:5d50`, source `0x23b30`)
pushes `0x43424d50` at `5d6d` and calls `0003:c316` at `5d7d`.
`0003:c316` (Ghidra `1010:c316`, source `0x2a0f6`) gets the record length at
`c344`, adds four bytes when the type halves match `CBMP` at `c367–c372`,
prepares a buffer through `0002:9150`, and reads the resource via `0001:7818`
at `c39b`. It is a generic resource-buffer path also used by PSND. Its CBMP
consumer calls `0002:4926` → `0002:4502` → frame routines `0002:455e/464e`,
then `0003:698e` → packed reader `0003:62e2`. Selected image layout, compression,
palette and border comparison are now in [formats/CBMP.md](formats/CBMP.md).
**Unknown:** the four extra allocation bytes' meaning, general compositing and
transparency, and coverage of other CBMP variants.

**Observed PSND path:** three original immediates `44 4e 53 50` at executable
file offsets `0x2c02e`, `0x2c114`, `0x2c141` were inside initially undefined
Code3 bytes. A method table at NE `0006:883a` (Ghidra `1028:883a`) contains the
relocated far pointer at `883e` to NE `0003:e1ee` / Ghidra `1010:e1ee`. Original
slot bytes at file `0x4d7fe` are `ee e1 44 88`; imported bytes are `ee e1 10 10`.
The segment fixup record at file `0x4ebb0` is `02 00 04 9b 03 00 00 00`; its
source chain includes selector word `0006:8840`, targeting NE segment `0003`.
Thus `1010` is the loader's analysis selector, not a source runtime selector.

Bounded disassembly at the method entry added `0003:e1ee–e463`; it has an
`ENTER 0x4c` prologue and multiple `RETF 8` exits. Its PSND pushes occur at
`e24c`, `e332`, and `e35f`. The first path obtains a file slice via `0001:7dd2`
at `e269`. Another gets length at `e340`, calls generic buffer routine
`0003:c316` at `e370`, and passes the buffer to `0004:0ef0` at `e3b3`. The
method branches on values `0x3ea/0x3ed/0x3ee`; their meaning is unknown. One
branch also calls the sequencer/file path `0003:916e`. This establishes a
selected-type consumer lead, not a PSND format or playback contract.

## Saved annotations, checks, and reproduction

`AnnotateArchive.java apply` persists the eleven names/comments above and four
types under `/YukonTrail/ObservedArchive`: explicit `OffsetSelector16` pairs,
8-byte group rows, 14-byte record rows, and a partial `0x70c` context with
unexplained fields left undefined. These are in-memory types, not direct
on-disk schemas. Fixed-width `dword` fields are used for lengths/offsets:
Ghidra's machine-sized `uint` shrinks to two bytes in this 16-bit program.
The saved audit explicitly verifies each actual field width. Function signatures
remain default guesses; segment pointers are not replaced by flat pointers.

The annotation script also reproduces only the two bounded missing functions
(`0003:e1ee` referenced by the method table, `0001:7dd2` by its direct call),
checking executable identity, prologue bytes, and the relocated method slot.
A pre-annotation project copy is retained locally at
`local/ghidra/backups/archive-trace-before/`.

Run from the repository root with the existing pinned toolchain and project.
Do not open the project concurrently in another Ghidra process. For a fresh
import, use `ANALYSIS.md` first. New output names preserve previous evidence:

```sh
python3 tools/ghidra/verify_lookup_trace.py original/extracted/windows/YUKONRES \
  > local/ghidra/lookup-trace-verification.json
yukon_root="$PWD"
tools/ghidra/headless.sh "$yukon_root/local/ghidra" YukonTrail \
  -process YUKON.EXE -noanalysis \
  -scriptPath "$yukon_root/tools/ghidra" \
  -postScript AnnotateArchive.java apply "$yukon_root/local/ghidra/new-annotation-audit.tsv" \
  -postScript TraceArchive.java "$yukon_root/local/ghidra/new-archive-trace" \
  -log "$yukon_root/local/ghidra/new-annotation.log"
tools/ghidra/headless.sh "$yukon_root/local/ghidra" YukonTrail \
  -process YUKON.EXE -noanalysis -readOnly \
  -scriptPath "$yukon_root/tools/ghidra" \
  -postScript AnnotateArchive.java verify "$yukon_root/local/ghidra/new-reopen-audit.tsv" \
  -postScript TraceArchive.java "$yukon_root/local/ghidra/new-reopen-trace" \
  -log "$yukon_root/local/ghidra/new-reopen.log"
cmp local/ghidra/new-annotation-audit.tsv local/ghidra/new-reopen-audit.tsv
cmp local/ghidra/new-archive-trace.asm.tsv local/ghidra/new-reopen-trace.asm.tsv
cmp local/ghidra/new-archive-trace.leads.tsv local/ghidra/new-reopen-trace.leads.tsv
```

**Actual save/reopen result:** a fresh JVM verified eleven names/comments, four
types and their actual field widths, and both added function boundaries. The
47-record annotation audits are byte-identical (SHA-256
`1ea63c8bbf30ef063e05805f0c993f5b00b1f84260934cfb4e7e7c2af90c37fa`). The
saved pair is `local/ghidra/archive-annotation-final-audit.tsv` and
`local/ghidra/archive-annotation-final-reopen-audit.tsv`; earlier audit files
predate the final comment wording. The
57,464-instruction relocated assembly and 55 lead records also match after
reopen; hashes are `094ff4f7fdaeec479421f2b65a4db7c6303df7fe90b0023d499ed5b371bcdd4e`
and `4a7bfd85fc6c85cef08d4524ef43f0ec2843a3672b44d91bc962b8d46f61700e`.
The source stamp remains verified. Source media were not changed.

Independent source-byte review checked sixteen nonrelocated instructions in
the header/group/record arithmetic and tag comparison at NE `0001:740c,749e,
74a2,74fc,7515,7531,7537,7539,753b,753d,753f,75b8,75d1,75e8,760c,7617`;
all matched the original bytes at segment file base `0x460` plus offset. The
report is retained in `local/evidence/archive-reader-source-check.json`. This
does not check relocated operands or dynamic DS. Decompiler probes completed
but still contain guessed arguments and unresolved segment registers; the
disassembly is the basis of the findings above.

**Next concrete action:** trace selected PSND resource-to-scene use and compare
a live original clip; sequential conversion and source parameters are now in
[formats/PSND.md](formats/PSND.md). The original is available for comparison.
Follow up CBMP color-key/clipping behavior and additional
variants separately. The full postread interpreter is still pending for the
registered resource types. New recovery names/layouts and their save/reopen
check are documented in [formats/CBMP.md](formats/CBMP.md).
