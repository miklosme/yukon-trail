# Original Windows save container

Checked2026-10-13. Observed fixed transfer layout, with byte-preserving parser and
original-instruction transfer checks. This is not complete save validation,
Windows load/scene reconstruction or browser persistence.

## Source and layout

EXE SHA256 `9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`.
NE1 maps to Ghidra1000, source file base0x460. Read function NE1:974a
(file0x9baa), write NE1:97ec(file0x9c4c); raw state is DS5308 far pointer,
journal object DS5304 has journal buffer far pointer at+0e. Both functions
transfer five consecutive blocks with no byte-order conversion:

| File offset | Length | Source buffer / observed content |
| --- | --- | --- |
| 0 | 5 | passed object+4; observed `MECC` plus NUL |
| 5 | 64 | passed object+9; observed `The Yukon Trail` plus zero padding |
| 69 | 10 | passed object+49; observed `0.1` plus zero padding |
| 79 | 902 /0x386 | complete raw state buffer |
| 981 | 10240 /0x2800 | complete journal buffer, including bytes after first NUL |

Total11221bytes, matching all five preserved original saves. The parser accepts
only the recovered current-version header branch and exact size. Header padding
is retained rather than required to be zero. Older-version restore is explicitly
unsupported; the original loader's full warning/restore policy is not recovered. Unknown state fields and journal tail bytes are retained intact.
Journal text is exposed as bytes rather than a guessed Unicode code page.
Unterminated journal text fails explicitly when requested; byte-preserving
container reading remains possible.

Read974a calls original8d88; write97ec calls original8e24. Those wrappers pass
handle, far buffer and low-word byte count to file APIs, compare returned count
to requested DWORD and have a separate error-message path. Close8d70 reaches
KERNEL::_LCLOSE. Original success return does not prove all OS errors are handled
or make a damaged save acceptable. Function9698 resets headers/state/journal;
it is not the five-block file reader itself. Load94e6 checks8854, clears selected global words, reads all five blocks, closes
the file, then validates the headers. Thus the original read occurs before the
header decision; any rollback/reset after an invalid file and subsequent scene
recreation remain unrecovered. Do not infer transactional restore from the parser.

## Independent checks

`verify_save_native.py` executes unchanged NE1:974a/97ec and their8d88/8e24
count-checking wrappers. Only the file-open/dialog call and actual KERNEL read,
write and close calls are replaced by an in-memory file, with explicit synthetic
selector relocation. The original instructions choose transfer order, buffer
pointers and counts. All five finalized evidence saves transfer and round-trip
exactly. Actual native block hashes and full source-save identities are retained
in [save-container-recovery-evidence.json](../save-container-recovery-evidence.json).
No source save or live guest file is written.

The Seattle saved raw words independently confirm day24/month8, cash422,
food2400, partner4, location(200,0,2000), matching native051/083/100. The three
White Pass saves confirm recorded predeparture, Skagway and after-theft states.
The blind save is also read without mutation. This bridges previously isolated
state-word recovery to actual saved state; it does not prove every hidden field.
RNG seed/global unsaved dependencies and journal tail significance remain unknown.

Python `tools/yukonsave.py` has five independent synthetic tests for fixed
boundaries, unsupported edition/length, opaque-byte preservation and journal
termination. `web/rules/save.ts` matches actual native block/full-file hashes
for all five evidence saves in Node26.0.0, preserves caller buffers and rejects
unsupported sizes/headers. Neither module allocates invented game defaults or
provides a browser File menu action yet.

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_save_native.py \
  original/extracted/windows/YUKON.EXE docs/save-container-recovery-evidence.json \
  local/evidence/seattle-reference-2026-10-13/SEATTLE-after-whipsaw-outfit.GAM \
  local/evidence/blind-playthrough-2026-10-04/BLIND-before-sheep-camp.GAM \
  local/evidence/white-pass-reference-2026-10-13/WHITE-predeparture.GAM \
  local/evidence/white-pass-reference-2026-10-13/WHITEA-Skagway.GAM \
  local/evidence/white-pass-reference-2026-10-13/WHITETR-after-theft.GAM
python3 -m unittest discover -s tests -p test_yukonsave.py
bun tests/test_browser_save.ts
```

Python3.14.5, pinned Unicorn2.1.4; no native arithmetic/state behavior stub is
used because these functions only transfer the existing buffers. The earlier container checkpoint
recorded five function names/comments surviving a separate
read-only Ghidra12.1.4/JDK21.0.12.1+1 JVM: identical11-record audits, SHA256
`05de49e93887fd19194300e11c007a217bb21ebaa757a4fb057b19eb6c093ea8`. Backup:
`local/ghidra/backups/save-container-before-20261014.tar.gz`.
No guessed function signatures/types are installed. Source instructions were
checked against current saved disassembly, including callers and wrappers;
useful transfer findings are versioned here instead of relying on temporary exports.

Reproduce annotation persistence with the established `tools/ghidra/headless.sh`
launcher, `-process YUKON.EXE -noanalysis -scriptPath "$PWD/tools/ghidra"`, first
`-postScript AnnotateSaveContainer.java apply AUDIT`, then a fresh invocation
with `-readOnly -postScript AnnotateSaveContainer.java verify AUDIT`. Compare
audits byte-for-byte. The native verifier reproduces transfer evidence; retain
the separate annotation audit fields when rebuilding the versioned report.

## Recovered header decisions

Original NE1:95a9..95ca,9614..9670 calls NE6:2004 (Ghidra1028:2004,
file0x46fc4). It compares unsigned bytes up to the supplied bound or the first
NUL in the loaded field, inclusive. Signature comparison uses only four bytes:
`MECC`; the fifth byte is ignored. Title is bounded64, version10. Post-NUL
padding is ignored. Version comparison is lexical rather than numerical:
`0.10` compares newer than `0.1` because its fourth byte is not NUL.

| Decision | Original status word | Original nonzero-message index |
| --- | --- | --- |
| signature mismatch | -1 | 5 |
| title mismatch | -2 | 6 |
| version compares lower | 1 | 4 |
| version compares higher | -3 | 7 |
| current header | 0 | none |

The numerical status/message-index routing is source-observed. Message text,
older-version migration/restore and error UI behavior are separate and pending.
Constructor92fe..9322 copies literal title/version from Data13:0dd2/0dce
(file0x501f2/0x501ee) to runtime globals564a/5640 through original1fda.
Native verifier executes those copies and the original header comparisons,
stopping at the common status branch before the message/UI actions. No comparison,
formatting or header rule is stubbed. Synthetic selector relocation is explicit.

[save-header-recovery-evidence.json](../save-header-recovery-evidence.json)
retains246 measured cases: each of79 loaded header bytes replaced independently
with0/65/255, source current header and eight explicit version strings. Python
and Node match every original status; both preserve ignored bytes on accepted
current saves. Older status1 fails explicitly in the supported container reader
because the subsequent original restore behavior is unknown.

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_save_header_native.py \
  original/extracted/windows/YUKON.EXE docs/save-header-recovery-evidence.json
bun tests/test_browser_save.ts
```

Next: trace load orchestration and scene restoration after the return status,
exercise original cancellation/corruption/short-file behavior in an isolated
reference copy, then connect actual game-state/journal restoration to browser
services through the original File controls. Do not add a new save dashboard or
claim a browser save round trip from these transfer/header checks.

Header follow-up annotations: all seven names/comments survive fresh Ghidra
reopening, identical15-record audits, SHA256
`75ba7b482f7087c2ff2b6aa97b28839f70dfbfb0537518751b0ce6619bf3bf1f`. Source header function94e6 was
disassembled/created at the verified prologue before annotation; an earlier
read-only probe had not persisted that function. Backup and apply/reopen paths
are retained in save-header-recovery-evidence.json.
