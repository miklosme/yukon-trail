# Original indexed image composition

Checked 2026-10-13 against Windows `YUKON.EXE`, SHA-256
`9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`.
All NE segment:offset addresses below retain the Ghidra mapping. This records
original copy kernels and the selected bubble drawing trace; it does **not** assign PNG alpha
to every CBMP. The Seattle Wharf palette discrepancy is explained below,
with a separate limitation on direct capture of GDI palette API returns.

## Observed copy kernels

| Operation | NE address | Ghidra | Source file offset |
| --- | --- | --- | --- |
| Copy except supplied index | `0001:0344` | `1000:0344` | `0x7a4` |
| Reverse source copy except supplied index | `0001:04fc` | `1000:04fc` | `0x95c` |
| Unconditional rectangle copy | `0001:042a` | `1000:042a` | `0x88a` |
| Normal zero-key wrapper | `0003:0d90` | `1010:0d90` | `0x1eb70` |
| Reverse zero-key wrapper | `0003:0e4c` | `1010:0e4c` | `0x1ec2c` |
| Clipped zero-key buffer composition | `0002:5c54` | `1008:5c54` | `0x14f14` |

**Observed disassembly:** `0001:0344` loads the excluded source byte from
`BP+1e` into AH at `035b`, source DS:ESI from `BP+0a`, destination ES:EDI from
`BP+06`. Width and height are dwords at `BP+0e/+12`; row strides are dwords at
`BP+16/+1a`. It compares each source byte with AH and skips destination writes
on equality (e.g. `0384–03bb`, remainder `0410–0420`). `0001:04fc` implements
the same excluded-byte condition while decrementing the source cursor.

The wrappers explicitly push zero at `0003:0d9f` and `0003:0e5b`, then call
those kernels at `0dc5` and `0e81`. `0002:5c54` clips rectangles and invokes
normal/reverse wrappers at `5eaa/5e93` according to its flip byte. This is
observed zero-index transparency **in that drawing path**. The separate
`0002:515a → 0003:0c56 → 0001:042a` path copies bytes unconditionally.

**Independent original-code check:** `tools/verify_image_copy_native.py`
executes both original excluded-byte kernels and the unconditional copy kernel with synthetic buffers. Widths1–9,
heights1–3 and keys0/37/255 produce243 comparisons with zero mismatches.
Independent expected bytes leave destination203 untouched at key positions,
copy other bytes, and preserve three padding bytes per row. Reverse source
ordering is separately checked. The unconditional kernel separately checks
that source zero overwrites destination203, unlike a zero-key composition. This covers short unaligned rows and remainder
branches, not huge segmented buffers, clipping, actual resource callers or GDI.
Ignored report: `local/evidence/recovery-proof/image-copy-native.json`.

## Observed CBMP postdecode normalization

`0002:464e` (Ghidra `1008:464e`, file `0x1390e`) decodes frames, then scans
its output rows. At `47c7–47d9` it changes indices1–9 and245–255 to120, retaining
zero. Specifically zero jumps to the unsigned `<=244` check and is preserved;
nonzero values below10 and values above244 are replaced. The existing bounded
asset decoder preserves packed indices; this native postdecode step is separate
from decompression. All256 possible bytes independently match execution of the original
`47c4–47dc` snippet through `tools/verify_image_normalization_native.py`.
Derived table SHA-256 is
`213efc9f0cc86ac59dcdf891b015b1f57c0855c60b21688ce42b65b812780e62`.
`tools/yukonrender.py` provides an explicit opt-in `windows_display_indices`
transform; it does not change lossless decoder/export output. Row iteration,
padding and full native-pixel effects remain untested. Do not silently fold it into lossless exports.

## Selected bubble consumer trace

**Observed static chain:** dialogue constructor `0001:0724` requests cache
IDs1/2 from DS:`56d4` at `09c1–09c9` and `0a46–0a4e`. Startup
`0003:5ddc` creates that server, installs table NE`0006:7b02`, and writes
DS:`56d4` at `5e12`. Relocated table slot4 points to `0003:5d50`, which pushes
CBMP tag`0x43424d50` at`5d6d` and constructs the CBMP object via
`0002:4926` at`5daa`. Thus these cache IDs are CBMP1/2, not merely numeric
coincidences. The CBMP constructor installs table NE`0006:67ea`.

The bubble sprite constructor `0002:e3b8` installs table NE`0006:71e8` and
initializes flip byte`+2c` to zero. Table slot`+0c` points to sprite update
`0002:e554`. Original scene-manager startup `0001:709a` uses `0002:da7c` with
zero at `7094`. That constructor delegates to `0002:38d4`, which creates
manager image buffer`+4` through `0002:4e4e` at`39b6` and omits alternate
buffer`+8` for its zero flag. `4e4e` installs image-buffer table
NE`0006:69ca` at`4e79/4e7e`. The scene-manager table NE`0006:706a`
slot`+14` resolves to redraw routine `0002:4290`.

At `0002:430e–431b`, manager redraw pushes its`+4` image buffer as the argument
to sprite virtual slot`+0c`. Bubble update `e554` pushes that same far pointer
from `BP+0a` at`e58e`, position far pointer, frame index from sprite`+2a`, zero
word, flip byte from sprite`+2c`, and CBMP object from sprite`+5a`; it then
invokes resource slot`+30` at`e5ae`. Relocated CBMP table`67ea+30` resolves to
`0002:7eb0`. Its destination remains `BP+14`; it forwards that object and flip
byte`BP+0a` to destination virtual slot`+34` at`7f79`. Relocated buffer table
`69ca+34` resolves to `0002:5c54`, whose normal branch calls the explicit
zero-key wrapper `0003:0d90`. This completes the selected static bubble path
to **source index-zero exclusion**, including the actual destination table.

**Scope:** this validates zero-index composition for these bubble sprites in
the original startup manager's normal redraw path. It does not validate every
CBMP drawing mode, the separate alternate-buffer sprite slot8 path, complete
clipping/position behavior, text, or the final GDI display. Full native bubble
pixels have not yet been compared; the original6,230-border-pixel check remains
scoped as recorded in [formats/CBMP.md](formats/CBMP.md). The Wharf background uses the different unconditional path described below.

## Seattle Wharf: copied index zero and system palette replacement

**Observed source:** `CBMP:4000` at archive offset`0xa05612`, length116,903,
payload SHA-256`bf44bb0de9cb9ec6c640ea251f9207a0eb0b7d230a8388dbd51ee3796ab1dd1b`,
frame0 is608×400. Its63 source-zero pixels all lie in column0, rows124–221.
All63 corresponding pixels in native capture`reference/krnl386_006.png` at
origin`(20,59)` are RGB`(0,0,0)`;45 fall inside the original top600×200 check.
The archive/source identities and selected native capture remain unchanged.

**Observed background copy path:** scene loader `0002:0002` reads the first
loaded SCNE word at`0353`, supplies it as a CBMP server ID at`0364`, and invokes
scene-manager slot`+20` at`03a0`. Raw SCNE4000 at archive`0x51be07d`, length10,
begins big-endian4000 (`0fa00fa00fa00fa00000`); complete SCNE/postread format
recovery is outside this finding. Manager table NE`0006:706a` slot20 resolves
to `0002:3ee2`. It selects the background frame through resource slot3c and
calls its image buffer's slot20 at`3f70`. Buffer table69ca slot20 resolves to
`0002:515a`, then `0003:0c56 → 0001:042a`. This **unconditionally copies zero**.
The243 original-kernel checks include81 cases for this unconditional copy.
There is no transparent-zero skip in this background install operation.

**Observed palette path:** embedded palette entry0 is white, but original
palette loader `0001:5eb4` replaces its first10 entries with
GETSYSTEMPALETTEENTRIES at`5fca`, then entries246–255 at`5fe1`. It creates the
replacement palette at`5ff4`, stores it in DS:`00ac`, and realizes it at
`600c/6015`. Startup`0001:7005–7017` puts that replacement handle into the
palette wrapper DS:`530c` through `0002:da0e`; wrapper field`+6` holds the handle.
The display initializer `0002:6a66` copies that field into its context at`6af1`
and SELECTPALETTE uses it at`6b02/6b42`. It constructs an identity logical-index
BITMAPINFO table at`6cbd`. Scene-manager display flush `0002:3dc8` passes the
same background buffer to `0003:0b92` at`3e8a`, then the GDI draw routine
`0002:6112`. Thus raw embedded RGB0 white is not the palette value used for
these zero pixels. A global CBMP zero-alpha rule would be the wrong explanation.

**Inferred from that code plus native pixels:** the configured Win31/S3 runtime's
replacement system entry0 is black. No separate GETSYSTEMPALETTEENTRIES-return
or DAC-register trace was captured. We explicitly supply reference RGB0 black
in the comparison; we do not present it as an independently dumped full palette.
The remaining nonreserved entries use the source RGB and recorded DAC conversion.

**Actual comparison:** with the independently checked postdecode index
normalization and the explicitly supplied reference system RGB0 black, all
120,000 top600×200 pixels and all400 pixels of source column0 match the native
capture. This removes the45 differences caused by the raw-palette assumption.
It verifies a static background region, not actors or the full scene. An
exploratory top600×250 comparison has2,139 mismatches beginning at`(193,208)`
inside an overlaid figure; it is not used as a passed background comparison.
The black-entry value is constrained by these native pixels and the system
replacement path; direct API-return capture remains a distinct unchecked step.

Reproduce explicitly (default CLI behavior still compares lossless source indices
and the embedded palette):

```sh
python3 tools/compare_background_capture.py original/extracted/windows/YUKONRES \
  original/extracted/windows/YUKON.EXE local/evidence/reference/krnl386_006.png \
  local/evidence/recovery-proof/wharf-system-palette-top.json \
  --id 4000 --x 20 --y 59 --rect 0,0,600,200 \
  --windows-display-indices --system-palette-zero-rgb 0,0,0
python3 tools/compare_background_capture.py original/extracted/windows/YUKONRES \
  original/extracted/windows/YUKON.EXE local/evidence/reference/krnl386_006.png \
  local/evidence/recovery-proof/wharf-system-palette-left.json \
  --id 4000 --x 20 --y 59 --rect 0,0,1,400 \
  --windows-display-indices --system-palette-zero-rgb 0,0,0
```

## Reproduction and persistence

Python3.14.5, Ghidra12.1.4 and project-local JDK21.0.12.1 were used.
Unicorn2.1.4 is staged as documented in [formats/CBMP.md](formats/CBMP.md).
The bounded emulator check needs the same approved unsandboxed execution used
by the existing native reader verifier because sandbox memory mapping faults.

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_image_copy_native.py \
  original/extracted/windows/YUKON.EXE \
  local/evidence/recovery-proof/image-copy-native.json

tools/ghidra/headless.sh "$PWD/local/ghidra" YukonTrail \
  -process YUKON.EXE -noanalysis -readOnly -scriptPath "$PWD/tools/ghidra" \
  -postScript AnnotateImageCompositing.java verify "$PWD/local/ghidra/compositing-reopened.tsv"
```

Thirteen supported kernel/wrapper/compositor/display names and comments were saved with
`AnnotateImageCompositing.java apply` after ignored backup
`local/ghidra/backups/compositing-before-20261013.tar.gz` and later
`compositing-chain-before-20261013.tar.gz`. A separate JVM verified all thirteen
and produced27 audit records SHA-256
`be231a873ae183d21379d885cb4d3bcdf8ee70ecb2214a9e63bccafb2acc09f7`.
No guessed signatures/types were installed.

`ProbeImageGap.java` is a read-only exploratory disassembly/export helper for
previously unanalyzed `0002:5158–5707`, selected relocated far-pointer tables, and optional
comma-separated Ghidra function addresses. Use `-readOnly` for exploratory runs so temporary function creation is discarded.
The documented annotation save used a backed-up writable run to retain the
three specifically established compositor functions before naming them. To reproduce the strongest
clipped-buffer lead:

```sh
tools/ghidra/headless.sh "$PWD/local/ghidra" YukonTrail \
  -process YUKON.EXE -noanalysis -readOnly -scriptPath "$PWD/tools/ghidra" \
  -postScript ProbeImageGap.java "$PWD/local/ghidra/compositing-gap.asm.txt" 1008:5c54 \
  -postScript DecompileSmoke.java 1008:5c54 "$PWD/local/ghidra/compositing-canvas-draw"
```

Next experiment: compare complete original bubble composition, clipping and
text with this statically established zero-key model. The actual native-pixel
check remains necessary; static dispatch and synthetic kernels do not substitute
for scene comparison.

Reproduce the full byte-normalization check:

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_image_normalization_native.py \
  original/extracted/windows/YUKON.EXE \
  local/evidence/recovery-proof/image-normalization-native.json
```

Selected Linda sprite placement and hotspot primitive validation are recorded in [SEATTLE-SPRITES.md](SEATTLE-SPRITES.md). This extends the selected zero-key drawing evidence to all visible nonzero pixels of the recorded frame; it does not validate the full scene or animation clock.
