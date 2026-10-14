# Bounded Windows CBMP recovery

Checked 2026-10-04. **Observed:** the original executable's frame reader,
packed integer readers, tile writer, and embedded display palette explain
`CBMP:1` and `CBMP:2`. A bounded decoder produces both 557×117 speech bubbles.
All integer-reader calls match execution of the original x86 routines;
6,230 border pixels from `CBMP:2` match the original ending capture.
This is a selected-image proof, not coverage of every CBMP or rendering mode.

## Source and code evidence

All executable addresses below refer to `original/extracted/windows/YUKON.EXE`,
404,272 bytes, SHA-256
`9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`.
Archive: `original/extracted/windows/YUKONRES`, 87,911,322 bytes, SHA-256
`438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`.
The imported analysis selectors are Ghidra mappings, not guest selectors.

| Operation | Original NE | Ghidra mapping | Segment file base |
| --- | --- | --- | --- |
| MSB bit reader | `0001:0000` | `1000:0000` | `0x460` |
| Escape integer reader | `0001:0062` | `1000:0062` | `0x460` |
| Hybrid integer reader | `0001:0129` | `1000:0129` | `0x460` |
| Frame table reader | `0002:455e` | `1008:455e` | `0xf2c0` |
| Frame extraction | `0002:464e` | `1008:464e` | `0xf2c0` |
| Packed expansion | `0003:62e2` | `1010:62e2` | `0x1dde0` |
| Local palette selection | `0003:66e8` | `1010:66e8` | `0x1dde0` |
| Cumulative palette | `0003:679e` | `1010:679e` | `0x1dde0` |
| Delta/reset palette | `0003:687c` | `1010:687c` | `0x1dde0` |
| Image write-context setup | `0003:698e` | `1010:698e` | `0x1dde0` |
| Column-major tile writer | `0003:6a28` | `1010:6a28` | `0x1dde0` |
| Embedded palette loader | `0001:5eb4` | `1000:5eb4` | `0x460` |

The generic resource loader path is in [ARCHIVE-CONSUMERS.md](../ARCHIVE-CONSUMERS.md).
Its postread registry contains neither CBMP nor PSND in the observed startup
registrations. Selected CBMP decoding uses unchanged archive bytes.

## Frame table and compression header

**Observed:** payload begins with a little-endian u16 frame count, then
12-byte frame records. Frame offsets are relative to the CBMP payload start.

| Frame-record offset | Width | Field |
| --- | ---: | --- |
| `+0` | 2 | Width |
| `+2` | 2 | Raw height |
| `+4` | 4 | Compressed chunk offset |
| `+8` | 4 | Compressed chunk length |

The proof supports positive width/height only. Signed/flipped rendering paths
are present but not validated. A compressed chunk begins with:

| Chunk offset | Width | Field |
| --- | ---: | --- |
| `+0` | 2 | Header size, 12 in the selected images |
| `+2` | 1 | Algorithm, 3 |
| `+3` | 1 | Flags, 1 |
| `+4` | 4 | Compressed bit count |
| `+8` | 4 | Expanded byte count |

At `header_size`, flags bit 0 supplies a byte containing global-palette length
minus one, followed by that many palette-index bytes. The subsequent bitstream
is MSB first. The declared bit count starts after this palette. Each decoded
block is 64 bytes. Expanded size for these images is
`ceil(width/8) × ceil(height/8) × 64`, including hidden edge padding.

## Block and palette decoding

Each block starts with two control bits:

| Value | Following fields | Meaning |
| --- | --- | --- |
| 0 | Local palette, two 3-bit width-minus-one fields, 64 escape-coded indices | Palette-mapped block |
| 1 | Same fields, 64 hybrid-coded indices | Palette-mapped block |
| 2 | 24-bit absolute bit position | Decode referenced block; restore outer cursor; discard its repeat count |
| 3 | 8-bit raw value, 1 repeat-present bit, optional 16-bit count | Fill block; count is additional copies |

Local palette selector is two bits for flags1: 0 uses the global palette;
1 and 2 read a 6-bit token count, two 3-bit width-minus-one fields, then
hybrid-coded tokens bounded by global-palette length minus one. For selector1,
selected index `i` is `sum(tokens through i) + i`. For selector2 the first
token is absolute; subsequent nonzero tokens add to the index; zero consumes
the next token as an absolute reset. Thus token count can exceed palette length.
Selector3 is unsupported by the proof tool and fails explicitly.

For escape coding, read `p` bits. An all-ones value escapes: add `e`-bit chunks
with byte wrapping until the result equals the allowed maximum or a chunk is
not all ones. Hybrid coding falls back to escape when `maximum >> p` is zero.
Otherwise, `p-1` small-value bits follow a leading 1. A leading 0 enters the
group code derived from NE `0001:0150–0298`:

```text
small = p - 1
low = (1 << small) & 255
k = e + small - 1
big_mask = ((2 << k) - 1) & 255
groups = min(32, (((maximum - low - big_mask - 1) >> k) + 2) & 65535)
limit = (groups - 1) & 255
```

Scan at most `limit` additional zero prefix bits until a 1, counting `j` zeros.
Read `k` suffix bits if `j < limit`, otherwise `k+1`; result is
`(low + (j << k) + suffix) & 255`. The original retains masks/results in bytes
and computes groups with signed word arithmetic followed by an unsigned cap.
Groups0 is valid; rejecting it incorrectly rejects a selected image's small
values. Default decompiler types obscure these widths, so disassembly and
original-code execution are authoritative. Uncovered extreme parameter
combinations are not claimed to be validated.

**Observed:** the image callback advances tile y first, then tile x. Within a
tile, pixels are row-major. The bounded decoder crops bottom/right padding.
Row-major tile placement produces incorrect strips despite consuming the right
number of bits; the original writer and native capture establish column order.

## Palette and rendering scope

NE `0001:5eb4` loads custom executable resource type 2000, ID100 through
FINDRESOURCE/LOADRESOURCE/LOCKRESOURCE. Raw file range `0x618e0 + 1056` contains
`RIFF` / `PAL ` / `data`, version `0x0300`, 256 entries, starting at resource+24
with stride4. At `5f44–5f76`, RGB bytes are copied to LOGPALETTE with entry flags4;
CREATEPALETTE follows at `5f8e`. A system-palette path also follows; the proof
does not assert every logical entry is always realized identically.
Extracted RGB SHA-256:
`9d51b54e203cc16dc9d5ccc7c6302baf945aecc9c5ac0b9a9ab1c8febf49297f`.

**Observed comparison:** CBMP2 at capture origin `(50,234)` matches all 6,230
border pixels, with zero mismatches, after mapping each source component by
`((v >> 2) << 2) | (v >> 6)`. **Inferred:** this corresponds to the configured
VGA six-bit DAC mapping; no DAC-register trace was performed. The comparison
uses original pixel positions, no resizing or automatic alignment.

Exterior index0 (11,610 pixels) and interior index159 (47,329 pixels) are
excluded: the native view contains scene background, dialogue and mouse pointer
in these regions. Their palette values are respectively `(255,255,255)` and
`(254,254,254)`. The exterior appears to be transparent in the native scene,
but its full color-key/compositing path remains **unknown**. PNG export preserves
all indices and RGB entries without inventing an alpha rule. Text, hit regions,
dialogue semantics, general transparency and clipping are outside this proof.

## Actual checks

Versioned metadata: [bitmap-recovery-evidence.json](../bitmap-recovery-evidence.json).

| Resource | Archive offset / length | Frame chunk offset / length | Packed bits / expanded bytes | Native integer calls |
| --- | --- | --- | --- | ---: |
| CBMP:1 | `0x74dd6` / 1,842 | 14 / 1,828 | 14,478 / 67,200 | 343 |
| CBMP:2 | `0x390a55` / 1,868 | 14 / 1,854 | 14,688 / 67,200 | 336 |

Both frames are 557×117 and consume exactly the declared bit count and expanded
size. All 679 integer-reader calls (165 unique input/parameter positions) match
the original output bytes and returned bit position. This independently checks
the primitives, not execution of the entire original frame-rendering function.
The separate native screenshot comparison checks the visible border composition.

25 new synthetic tests have hand-authored symbols/pixels: MSB order, escape and
hybrid branches, palette modes, references, repeat bounds, partial tiles,
column order, malformed data, indexed PNG preservation, capture filters/CRC,
and the comparison mask. Full suite after sound tests: 86 tests passed without game media.

14 supported names/comments and two observed layouts persist in Ghidra. A fresh
JVM reopened the saved project and produced the same 40-record annotation audit,
SHA-256 `4c991e0edc75ec5e4d73751b3ca64400f063af8ae854b893b072b85ae526fa5a`.
Original function parameter signatures remain unmodified. Pre-mutation backup:
`local/ghidra/backups/recovery-before-20261004.tar.gz`.

## Reproduction

From repository root, using Python 3.14.5 and the verified source files:

```sh
python3 tools/yukonbmp.py original/extracted/windows/YUKONRES \
  original/extracted/windows/YUKON.EXE generated/recovery-proof --id 1 --id 2
python3 tools/compare_bitmap_capture.py original/extracted/windows/YUKONRES \
  original/extracted/windows/YUKON.EXE \
  local/evidence/blind-playthrough-2026-10-04/12-ending-dialogue.png \
  local/evidence/recovery-proof/border-comparison.json --id 2 --x 50 --y 234
python3 -m unittest discover -s tests -v
```

Native capture SHA-256:
`5817f35362f2ddced25f9ec93952c9a11ac89a587a9c4945b1c682baa605c6ec`.
Its provenance is in [BLIND-PLAYTHROUGH.md](../BLIND-PLAYTHROUGH.md).
No new game run, save or guest reset was needed for this comparison.

Optional independent verifier uses official Unicorn 2.1.4 only in ignored
`local/tools/`. It is an analysis dependency, not a game/runtime dependency.
On this arm64 host, the installed wheel was obtained and checked as follows:

```sh
curl -fL https://pypi.org/pypi/unicorn/2.1.4/json \
  -o local/tools/unicorn-2.1.4-pypi.json
curl -fL https://files.pythonhosted.org/packages/6c/ae/4943c6f8524d729ec7d5e69df6407ea05d710fe77471d91cecf3fc64eb57/unicorn-2.1.4-cp37-abi3-macosx_11_0_arm64.whl \
  -o local/tools/unicorn-2.1.4-arm64.whl
shasum -a 256 local/tools/unicorn-2.1.4-arm64.whl
python3 - <<'PY'
from pathlib import Path
import hashlib, zipfile
wheel = Path('local/tools/unicorn-2.1.4-arm64.whl')
assert hashlib.sha256(wheel.read_bytes()).hexdigest() == 'd6c93e0f60328d8f4a1792af3f834137a28050fcc2305f2ec01efe8558a9844e'
destination = Path('local/tools/unicorn-2.1.4-python')
assert not destination.exists(), 'use a fresh destination'
with zipfile.ZipFile(wheel) as archive:
    assert archive.testzip() is None
    for member in archive.infolist():
        path = Path(member.filename)
        assert not path.is_absolute() and '..' not in path.parts
        assert (member.external_attr >> 16) & 0o170000 != 0o120000
    archive.extractall(destination)
PY
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_bitmap_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  local/evidence/recovery-proof/native-integers.json --id 1 --id 2
```

Wheel: 12,142,730 bytes; SHA matches published PyPI metadata. It has 47 members,
with CRC/path checks passing. No global install was performed. This host's
sandbox faults with SIGILL on Unicorn `mem_map`, even for two NOP instructions;
the same bounded probe succeeds outside that sandbox with approved execution.
No host security setting was changed. The verifier loads only original
NE1:0000–02d0 at a synthetic real-mode segment; scratch/input/stack regions are
separate. It executes no Windows/guest API and imposes an instruction limit.
These scratch selectors are test harness values, not recovered guest addresses.

Using the existing project-local Ghidra 12.1.4/JDK launcher:

```sh
tools/ghidra/headless.sh "$PWD/local/ghidra" YukonTrail \
  -process YUKON.EXE -noanalysis -readOnly -scriptPath "$PWD/tools/ghidra" \
  -postScript AnnotateRecovery.java verify "$PWD/local/ghidra/recovery-annotations-reopened.tsv"
```

For a fresh, source-verified import, back up the project first and use `apply`
with a writable run (omit `-readOnly`), then verify in a separate JVM.
`ExportResourceAPIs.java` records palette/DIB/wave API thunk callers read-only;
useful assembly/decompiler probes are reproducible through `DecompileSmoke.java`
at the addresses above. Ignored projects, PNGs, raw indices and logs stay local.

## Remaining work

PSND live playback comparison and one original-versus-recovered state operation
remain pending. Other CBMP variants, signed heights,
full palette realization and compositing need separate evidence. The bounded
decoder rejects unsupported headers and malformed indices/references; it does
not substitute guessed data. M1 remains incomplete and runtime selection stays
deferred.

## Archive census and Seattle image checks (2026-10-13)

**Observed decoder acceptance:** all 331 CBMP resources, containing 1,523
frames, pass the unchanged bounded decoder. All declared chunk headers are
size12/algorithm3/flags1; all frame dimensions are positive. The census preserves
resource offsets/lengths, payload hashes, raw frame tables and decoded index
hashes. It does not establish native rendering, all palette branches or
compositing correctness. Reproduce the deterministic report with:

```sh
python3 tools/audit_bitmaps.py original/extracted/windows/YUKONRES \
  local/evidence/recovery-proof/bitmap-census-20261013.json
```

Use a fresh report path. Full report: 794,182 bytes, SHA-256
`dd73cfc4fe800d8ebed7ef2a9e54633407b54330cfaf93790c0d11da6c0da10a`.
The summary and selected comparison identities are versioned in
[bitmap-census-evidence.json](../bitmap-census-evidence.json).

**Observed visual identification:** decoded frame0 of CBMP1000 shows downtown
Seattle; CBMP2000 the outfitter interior; CBMP3000 the ticket office; CBMP4000
Seattle Wharf. These identifications follow direct image inspection, not ID
numbering alone. Scene-resource linkage in the executable is not yet recovered.

**Observed original-reader comparison:** CBMP3000 (one608×400 frame) and
CBMP4001 (seven frames) produce 7,830 integer calls / 5,406 unique calls, all
matching original NE1:0062/0129 bytes and cursors. The harness remains bounded
to packed inputs at most60,000 bytes; larger background streams were not tested
with this verifier. The sandboxed attempt returned SIGILL, as previously
documented; approved execution outside that sandbox passed. This is isolated
integer-code validation, not the full frame/draw pipeline.

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_bitmap_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  local/evidence/recovery-proof/seattle-native-integers-20261013.json \
  --id 3000 --id 4001
```

**Observed bounded pixel comparison:** CBMP4000, archive offset `0xa05612`,
length116,903, payload SHA-256
`bf44bb0de9cb9ec6c640ea251f9207a0eb0b7d230a8388dbd51ee3796ab1dd1b`,
matches119,955 of120,000 pixels in source rectangle `(0,0,600,200)` against
`local/evidence/reference/krnl386_006.png`, origin `(20,59)`, with the same
explicit palette conversion used above. This region covers the static upper
wharf background above the foreground people; the lower half is not compared.
The decoded frame is608 pixels wide, while the native scene displays600 pixels.
The rightmost8 source columns are outside this capture comparison.

The initial origin `(20,60)` gave86,660 differences; a small offset probe on the
title area identified `(20,59)`, then the fixed-origin comparison above was
rerun. Record this as discovered alignment, not a pre-established layout rule.
All45 remaining differences are at source x0, index0: source palette RGB white,
native RGB black. Their cause remains **unknown** (a transparency/drawing-path
lead). The comparison exits1 and retains the discrepancy rather than assigning
an invented alpha rule or masking it into a success.

```sh
python3 tools/compare_background_capture.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  local/evidence/reference/krnl386_006.png \
  local/evidence/recovery-proof/wharf-background-20261013.json \
  --id 4000 --x 20 --y 59 --rect 0,0,600,200
python3 -m unittest discover -s tests
```

The added census/comparison tests use hand-authored tiles and RGB pixels, check
cropping, duplicate rectangle accounting, malformed tables and exact mismatch
detection. Full suite:91 tests passed. All16 extracted files also matched fresh
direct-disc reads using `tools/verify_source_files.py`. No source asset or
generated image is committed.

**Observed subsequent consumer trace:** selected CBMP1/2 bubble sprites reach
the original index-zero exclusion kernel through the actual scene-manager buffer
and its relocated method table. All162 synthetic copy-kernel cases and256
postdecode index-normalization inputs match original code.
[IMAGE-COMPOSITING.md](../IMAGE-COMPOSITING.md) records the complete static chain,
addresses, preserved annotations and the explicit optional display transform.
Lossless CBMP exports remain unchanged. This closes the selected static
transparency-path question, while full native composition, text, clipping and
the45 Wharf differences remain pending.

**Observed additional image/text case:** frame at nominal70 seconds in the
preserved `02-seattle-to-dyea.avi` visibly shows Linda and TREE616's exact storm
line. Its CBMP1 bubble at `(40,234)` matches all6,317 border pixels, zero
differences under the same palette conversion. The11,523 exterior and47,329
interior pixels remain excluded; no full-text or scene-composition comparison
is claimed. The AVI matches its preserved SHA-256
`9f9474e3efd04f2e80cb562250bf86bcf25ce49635d37c012c9562ca7d661966`.
The derived RGB frame hash is
`84b681ad06483629e0b7dd598c7014a0eba1499cdc94d1337df58bb7b0e00f72`.
This is a frame derived from native video, not a fresh original-game run.
Full metadata is in the census evidence linked above. Reproduce with:

```sh
ffmpeg -nostdin -v error -ss 70 \
  -i local/evidence/blind-playthrough-2026-10-04/02-seattle-to-dyea.avi \
  -frames:v 1 local/evidence/recovery-proof/voyage-storm-70s-20261013.png
python3 tools/compare_bitmap_capture.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  local/evidence/recovery-proof/voyage-storm-70s-20261013.png \
  local/evidence/recovery-proof/storm-bubble-20261013.json \
  --id 1 --x 40 --y 234
```
