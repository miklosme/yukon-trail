# Bounded sequential PSND recovery

Checked 2026-10-04. **Observed:** PSND1 expands to 81,792 unsigned 8-bit mono
samples at 22,050 Hz (about 3.7094 seconds). All 1,278 integer-reader calls and
all sample conversions agree with execution of the original x86 routines.
The source format and getter bindings establish the playback parameters.
**Unknown:** the original interaction that plays this resource. No live
resource-mapped playback comparison is claimed for PSND1. A 2026-10-13 follow-up
below adds bounded PSND616 recovery and a source-mapped original-capture
comparison. Seeking, looping and broader sample/compression parameters remain
unsupported.

## Source and address evidence

Archive `original/extracted/windows/YUKONRES`: SHA-256
`438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`.
PSND1: archive offset `0xbe2a4d`, length 45,300, payload SHA-256
`a671dfae45ada8f46ea6a9d8ce0042d53234106ec6c479e60590ca8f55b1fa40`.
Executable `original/extracted/windows/YUKON.EXE`: SHA-256
`9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`.
Code3 file base `0x1dde0`; Code6 base `0x44fc0`. Ghidra selectors below are
import mappings, not guest runtime selectors.

| Operation | Original NE | Ghidra |
| --- | --- | --- |
| Sound processor constructor | `0003:acea` | `1010:acea` |
| Header/index records | `0003:b3a2` | `1010:b3a2` |
| Packed stream constructor/header | `0003:b636/baae` | `1010:b636/baae` |
| Packed stream blocks | `0003:be0e` | `1010:be0e` |
| Shared packed block decoder | `0003:63fe` | `1010:63fe` |
| Byte integration | `0003:9b34` | `1010:9b34` |
| Playback format constructor | `0003:92dc` | `1010:92dc` |
| Playback open | `0003:978a` | `1010:978a` |
| Channels/bits/rate-code getters | `0003:b20a/b218/b226` | `1010:b20a/b218/b226` |
| Sound processor method table | `0006:82c0` | `1028:82c0` |

Consumer paths and the bounded postread no-match result are in
[ARCHIVE-CONSUMERS.md](../ARCHIVE-CONSUMERS.md). The file and memory paths both
feed stream-backed processing. Findings derive from raw bytes, disassembly,
callers, relocated getter slots and isolated execution; guessed decompiler
parameter signatures are not installed.

## Selected layout

PSND1's little-endian record sequence is:

| Payload offset | Type / raw flags | Length | Meaning established here |
| --- | --- | ---: | --- |
| `0` | 1 / `0x81` | 12 | Sample parameters and integration order |
| `0x0c` | 2 / `0x80` | 50 | Retained index/checkpoint metadata |
| `0x3e` | 0 / `0x80` | 6 | Data marker; compressed chunk follows |

The first six bytes are type u8, raw flags u8, record length u32. Header bytes:
`01 81 0c 00 00 00 01 08 16 01 02 19`.
Processor `0003:acea` copies bytes6/7/8/10 into object words `+1c/+1e/+20/+1a`.
These are channels1, sample bits8, rate-code 22 and integration order 2.
Bytes9/11 and full record-flag semantics are not interpreted.

The index count is a **word at record+8**, confirmed by `0003:b3cd`, not a
dword at+6. Selected count 5 gives `10 + 5×8 = 50` bytes. Entry meanings and
replay-state semantics are not implemented. They are retained in the decoder's
`Sound.record_metadata`, with their hash in its manifest. The tool performs
sequential expansion from the original initial state; it supplies no seek/loop
API and does not claim those behaviors.

At payload `0x44`, the compression header is the shared 12-byte layout from
[CBMP.md](CBMP.md), followed by additional header bytes: header size 54,
algorithm3, flags2, packed bit count 361,423, expanded byte count 81,792.
The additional 42 bytes are retained as `Sound.chunk_metadata`, not assigned
guessed semantics. The packed stream begins at payload `0x7a`.

**Observed:** `0003:baae` constructs the byte table
`128,127,129,126,130,125,…,255,0` and clears its local palette-control byte.
The two-bit block controls and integer primitives are shared with CBMP, but
there are no local palette-selector bits in this selected sound path. Symbol
indices map through that alternating table. PSND1 has 1,278 decoded 64-byte
blocks, with no reference/constant blocks in the observed sequential stream.
Expansion consumes exactly361,423 bits and yields exactly81,792 values.

## Sample conversion and playback parameters

NE `0003:9b34` receives a far four-byte state pointer (`BP+06`), order dword
(`+0a`), byte count dword (`+0e`), and far byte buffer (`+12`). It handles
orders 1–4. Initial state from `0003:ad15` is `[128,128,128,128]`. For each
expanded byte, the converter updates the deepest active state first, then
works toward state0:

```text
value = expanded_byte
for index = order-1 down to 0:
    state[index] = (state[index] + value + 128) & 255
    value = state[index]
sample = value
```

State persists across input buffers. The selected order 2 uses the branch at
`9b72–9ba2`. 8-bit arithmetic/wrapping is checked directly against disassembly
and original execution, rather than inferred from apparent audio quality.

The relocated processor method slots at Ghidra `1028:82f4/82f8/82fc` point to
`1010:b20a/b218/b226`. Their original NE slots are `0006:82c0+34/+38/+3c`;
source file offsets `0x4d2b4/0x4d2b8/0x4d2bc` contain pointer bytes
`0a b2 fa 82`, `18 b2 fe 82`, `26 b2 02 82`. The imported selectors become
`1010`, verified by the annotation script. The getters return words
`+1c/+1e/+20`, tying the header to channels, bits and rate-code.

At `0003:94bf–94ed`, playback constructor `0003:92dc` maps rate-code 11 to
11,025 and22 to 22,050. It writes format tag1 at object+44, channels at+46,
rate at+48, block alignment at+50 and sample bits at+52. Playback routine
`0003:978a` passes this format pointer to WAVEOUTOPEN at `9826`.
Thus PSND1's parameter interpretation is source-grounded: unsigned8-bit PCM,
one channel,22,050 Hz. Other parameter values/branches need separate checks.

## Validation scope and results

Metadata: [sound-recovery-evidence.json](../sound-recovery-evidence.json).

- Every1,278 integer decoding calls (all unique input positions) matches
  original NE `0001:0062/0129` bytes and returned cursor.
- All 81,792 converted samples, plus the four-byte final state
  `[128,129,128,128]`, match original NE `0003:9b34` execution. Buffers are
  at most16,384 bytes to preserve the original far-buffer boundary; state is
  retained across all five probe chunks.
- Independent wrap-heavy synthetic input checks all four original integration
  branches. Six standard-library tests check hand-calculated integration,
  retained state, default palette/no local controls, malformed/unsupported
  records and WAV parameters/samples. Full suite 86 passes without source media.
- Encoded-value SHA-256:
  `9ab91c8cd6a03fb6bf88992cd4ba7f0bc204046c00becccb3df53a8825f4b09d`.
  PCM SHA-256:
  `20becd1623eaa00da9bfdd8cb2808aee7375718c17243d22323b642bb4058d7f`.
  WAV SHA-256:
  `1ef6c8fb3a86e8d959b3c405218b026fe0025948928af0af4286320da1b9d115`.

These checks execute the original integer readers and sample converter, not
the entire sound processor, stream-window/seek logic, driver or live game.
The default-table mapping and format binding are independently read from the
executable. A live clip comparison remains necessary for the M1 checkpoint.

An exploratory4 kHz normalized waveform search of the two existing opening
captures did not find a convincing match: maximum correlations about 0.08935
and0.08835. This does **not** establish decoder failure or missing playback;
the resource might not occur there, or the search might miss mixer/clock effects.
No native-clip identification is claimed from those peaks. The next step is to
trace the resource's dialogue/scene use and capture that case deliberately.

## Reproduction

```sh
python3 tools/yukonsnd.py original/extracted/windows/YUKONRES generated/recovery-proof
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_sound_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  local/evidence/recovery-proof/native-sound.json
python3 -m unittest discover -s tests
```

The optional pinned Unicorn 2.1.4 staging, hashes and this host's sandbox mapping
limitation are in [CBMP.md](CBMP.md). The converter probe runs only the
nonrelocated byte range NE3:9b34–9c3f with synthetic scratch selectors, no guest
or Windows APIs, and an instruction limit. It preserves original media.
Scratch selectors are harness values, not recovered runtime selectors.

## Dialogue mapping follow-up (2026-10-13)

**Observed static routing:** PSND1 is referenced by the first response in
`TREE:1`, whose text is “I'm afraid we do not have enough money for that”.
This provides a deliberate live-capture lead; it is not yet an observed playback
case. The speaker identity and exact UI trigger remain to be checked in the
original. An unaffordable purchase after choosing the matching partner is an
**inferred** trigger, based on that text.

All findings use the archive/executable SHA-256 identities above. `CONV:1`
is at archive `0xbdc998`, length44, SHA-256
`a15b8b36908e21c3dd34170f7bdf2a5b8f06d0da3c841e1e0b569171488aa588`;
its word at+16 is1. `TREE:1` is at `0x51c2175`, length1,648, SHA-256
`985c4295e47595e266d1da976dd934000031e726023d11ce52d98fd0d6ba566e`.
It contains word1 at payload+0x126 and the quoted text at+0x128. The first
initial-text slot at+0x16 is empty, so its first response starts at+0x116.
Other TREE formats, condition meanings and full traversal remain unimplemented.

The checked disassembly chain is:

| Operation | Original NE | Ghidra mapping | Source file offset |
| --- | --- | --- | --- |
| Load TREE and set response cursor | `0001:1f02` | `1000:1f02` | `0x2362` |
| Copy response fields into node | `0001:1c56` | `1000:1c56` | `0x20b6` |
| Select displayed text and voice ID | `0001:2bc2` | `1000:2bc2` | `0x3022` |
| Sound/cache key dispatch | `0002:9cd6` | `1008:9cd6` | `0x18f96` |

1. `0001:2c9e` selects the CONV entry's word at+16+14×entry, and
   `0001:0724` calls the TREE loader with that result. The condition evaluator
   is not recovered; for CONV1 the candidate IDs are1 and0.
2. TREE loader `0001:1f02` scans at most five initial records, stride0x112,
   testing text at+0x16. It sets the response cursor to+0x116+0x112×count.
3. `0001:1cec–1cf6` copies response word+0x10 to allocated node+0x10.
   `0001:2c65–2c6c` copies that node word to conversation+0x24. The adjacent
   response text+0x12 is retained as the displayed text far pointer.
4. `0001:0d15–0d25` pushes conversation+0x24 as the low word (ID) and
   0x3ed as the high word (kind), with the sound-server far pointer at DS:009c,
   into `0002:9cd6`. Zero ID or disabled audio flags bypass this path.
5. Sound-server initialization `0001:6c7a–6c88` stores the object constructed
   by `0003:e1ae` at DS:009c. That constructor installs table `0006:883a`
   (Ghidra `1028:883a`); its slot+4 maps to `0003:e1ee`. On a cache miss,
   `0002:9e04–9e10` passes the unmodified ID/kind dword into this slot.
6. The previously traced `0003:e1ee` kind0x3ed branch obtains PSND length
   at `e340` and loads the resource at `e370`; the ID comes from BP+0x0a,
   while the kind is BP+0x0c. Thus selected TREE1 word1 reaches PSND1.

Nine nonrelocated routing instructions were independently compared against
direct executable bytes; all matched. The local report is
`local/evidence/recovery-proof/dialogue-sound-source-check.json`. This checks
static data flow, not runtime segment values or driver output.
Read-only decompiler/assembly probes are saved as `local/ghidra/mapping-*`.
Reproduce with the existing pinned Ghidra/JDK command, adding
`-postScript DecompileSmoke.java ADDRESS OUTPUT_PREFIX` for each table entry,
and `1000:0724` / `1000:2c9e`. Guessed decompiler types are not evidence.

`AnnotateDialogueSound.java` saves four supported names/comments without
altering signatures. The pre-mutation backup is
`local/ghidra/backups/dialogue-sound-before-20261013.tar.gz`. Apply and verify
in separate headless JVMs, using the command style above:

```sh
tools/ghidra/headless.sh "$PWD/local/ghidra" YukonTrail \
  -process YUKON.EXE -noanalysis -scriptPath "$PWD/tools/ghidra" \
  -postScript AnnotateDialogueSound.java apply "$PWD/local/ghidra/dialogue-sound-applied.tsv"
tools/ghidra/headless.sh "$PWD/local/ghidra" YukonTrail \
  -process YUKON.EXE -noanalysis -readOnly -scriptPath "$PWD/tools/ghidra" \
  -postScript AnnotateDialogueSound.java verify "$PWD/local/ghidra/dialogue-sound-reopened.tsv"
cmp local/ghidra/dialogue-sound-applied.tsv local/ghidra/dialogue-sound-reopened.tsv
```

**Actual persistence result:** the fresh JVM verified all four names/comments;
the nine-line apply/reopen audits are byte-identical. No parameter signatures
were changed and no original-game interaction was performed by this analysis.

Reproduce the exploratory opening-capture search using existing bundled
Python/NumPy 2.3.5 and FFmpeg 8.1.2; this is optional analysis tooling, not a
decoder or game dependency. The configured interpreter on this host is:

```sh
/Users/miklosme/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  tools/find_sound_capture.py generated/recovery-proof/PSND-1.wav \
  local/evidence/reference/krnl386_001.wav local/evidence/reference/krnl386_002.wav \
  --report local/evidence/recovery-proof/opening-sound-search.json
```

On another host, use a configured interpreter with NumPy available; no package
manifest was introduced. The tool uses FFmpeg to resample both inputs to 4 kHz,
removes the template mean, computes FFT cross-correlation and normalizes by
sliding-window mean-adjusted energy. It bounds captures at ten minutes and
reports candidate peaks without accepting them as identity matches. Capture
hashes, tool versions and peaks are retained in the versioned sound evidence.

Nine supported names/comments and one observed 12-byte record layout are saved
by `AnnotateSound.java`; the script also checks the three relocated getter
bindings. Back up before `apply`, then verify in a fresh read-only JVM:

```sh
tools/ghidra/headless.sh "$PWD/local/ghidra" YukonTrail \
  -process YUKON.EXE -noanalysis -readOnly -scriptPath "$PWD/tools/ghidra" \
  -postScript AnnotateSound.java verify "$PWD/local/ghidra/sound-annotations-reopened.tsv"
```

Pre-sound annotation backup: `local/ghidra/backups/sound-before-20261004.tar.gz`.
Fresh JVM verification retained all 30 annotation records, SHA-256
`932016061ab71b29fbadd04d276c594f1c9948187abc8fef251a72e0a415bab7`;
the existing40 image-recovery records remain unchanged.
Additional assembly probes use `DecompileSmoke.java` at `1010:be0e`,
`1010:9b34`, `1010:92dc`, and the getter addresses. Saved parameter signatures
remain unmodified. Decoder outputs, samples, WAVs, projects and dependencies stay
in ignored locations; versioned files contain tools, tests and evidence metadata.

## Selected Linda storm clip (2026-10-13)

**Observed:** `TREE:616` first response has voice word616 at payload+0x126,
with the storm text at+0x128. The raw resource starts with speaker word4,
matching Linda's interview `CONV:3400`. The static voice routing described
above reaches `PSND:616` through kind0x3ed's memory-stream path. The same
storm text and Linda portrait are visible in the original voyage frame at
nominal70 seconds. This scene/text observation, binary mapping, native decoder
comparison and aligned waveform together support the selected clip mapping.
They do not establish full mixer or general audio fidelity.

Source identities are the archive/executable hashes above. `TREE:616`:
archive `0x5348ff1`, length1,648, SHA-256
`5d6ab820f9e71ffb4cb321b1faf25b6a42a42362bd061ab7da8f10f344f87fdc`.
`PSND:616`: archive `0x486a8ac`, length48,177, SHA-256
`1e21aaf8ca331179cd7aed849a76b911f2f57ee040766e6ba291f1aa2d789388`.
Its first12 bytes are `01 00 0c 00 00 00 01 08 16 01 01 39`: channels1,
bits8, rate-code22, order1. The index record at+12 is type2, raw byte1=0x81,
length50/count5. The data record at+62 is type0, raw byte1=0x84, length6.
Chunk at+68 has size54/algorithm3/flags2, packed384,435 bits and declared
expanded82,134 bytes. Byte9/11 and checkpoint metadata meanings are retained
as unknown; they are not assigned new semantics.

### Record byte1 and final-block boundaries

**Observed:** PSND byte1 is not interpreted on this selected memory-stream
processor path. `0004:0ef0` (Ghidra `1018:0ef0`, source `0x2d9b0`) installs
table `0006:89fc` / `1028:89fc`. Its relocated slot+0x18 at `1028:8a14`
is `1018:0f4c`. The raw source slot at `0x4d9d4` is `4c 0f 1a 8a`, with
NE segment relocation, not a runtime flat pointer.

Getter `0004:0f4c` / `1018:0f4c`, source `0x2da0c`, returns the buffer+cursor
far pointer and length−cursor, without reading payload bytes. Processor
`0003:acea` reads type byte0, length dword+2 and selected parameters at
bytes6/7/8/10; it never reads record byte1. The type2 consumer likewise
uses record length/count/index entries, without byte1. The byte is therefore
retained uninterpreted in raw record metadata; this is not proof of what
the original author intended it to mean.

The file-stream constructor installs table `0006:9afe`; its slot+0x18 maps
to `0005:8eaa` / `1020:8eaa`. It returns a buffered pointer/remaining length
after refill `0005:9168`, checking internal buffer-control bytes+0x10/+0x11.
Those internal fields are distinct from PSND record byte1. Full file refill
and seek behavior remain unexecuted by this proof.

`tools/verify_sound_stream_native.py` executes unchanged getter `0004:0f4c`
for all256 byte1 values and cursor0/end: **512 cases, zero mismatches and
zero payload reads**, observed with Unicorn memory-read hooks. It checks the
returned far pointers, lengths and status against independent expected values.
[The small native stream report](../sound-stream-recovery-evidence.json)
records source/code/row hashes and scope.

`0003:baae` at `bb72–bb85` computes `(expanded+63)/64` for the packed block
count. `0003:bbee` at `bc03–bc25` clamps emitted byte count to expanded−cursor.
PSND616 expands1,284 complete64-byte blocks, consuming exactly384,435 bits.
Only82,134 values become samples; the final42 packed block bytes are retained
as `Sound.block_padding`, excluded from conversion/output. The decoder now
supports this selected final partial block, order1/2 with mono8-bit rate22,
and uninterpreted byte1 values. Header size54 remains required; other header
sizes, formats, seeking and looping still fail or remain unsupported.

**Actual native result:** all1,284 integer-reader calls and all82,134 converted
samples/final state `[129,128,128,128]` match original code. PCM SHA-256
`d26ff46d80ecc07fa358f39b33f3c932d8c70c2d89d8a4592d8660d34f68542f`;
WAV SHA-256
`49099dae358c2a4d277527c8b7612ceab533f9fb6ddf7aa775d01a7d282dd3c5`.
[PSND616 native evidence](../sound616-recovery-evidence.json) records these
checks. The PSND1 follow-up still matches its original1,278 calls,81,792
samples and unchanged PCM/WAV hashes. Nine sound tests pass, including
all byte1 values, hand-calculated order1 vectors and partial-block bounds.

### Original capture comparison and residual

Original `local/evidence/blind-playthrough-2026-10-04/02-seattle-to-dyea.avi`,
SHA-256 `9f9474e3efd04f2e80cb562250bf86bcf25ce49635d37c012c9562ca7d661966`,
contains48,000Hz stereo16-bit captured PCM. The observed native storm frame
`local/evidence/recovery-proof/voyage-storm-70s-20261013.png`, SHA-256
`84b681ad06483629e0b7dd598c7014a0eba1499cdc94d1337df58bb7b0e00f72`,
shows Linda and the exact TREE616 line; root and the sound subagent inspected it.

After explicit FFmpeg conversion of both inputs to4kHz mono, the selected
3.725-second resource aligns at **69.01675–72.74175 seconds**. Full-window
normalized correlation is **0.970498**; consecutive thirds give **0.962377,
0.969932,0.978548**. A fitted gain/DC comparison retains a **24.11% RMS
residual relative to capture RMS**. A separate within-one-sample phase refinement
(−0.3 of a4kHz sample, no time stretching) improves correlation to0.989638,
with14.36% residual; it does not erase the unrefined result.

This is strong selected-waveform agreement, with source decoder output and
independent text/frame timing as corroboration. It is **not bit-identical**
captured PCM. Differences in original mixer/filter/resampling and other mixed
audio have not been individually recovered or explained. Do not mark whole
audio fidelity complete from this comparison. The fitted gain is a measurement,
not a proposed port volume setting. [The full comparison report](../sound616-capture-comparison.json)
retains alignment, every-third consistency, gain/DC, residual and tool versions.

```sh
python3 tools/yukonsnd.py original/extracted/windows/YUKONRES \
  generated/recovery-proof-sound616 --id 616
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_sound_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/sound616-recovery-evidence.json --id 616
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_sound_stream_native.py \
  original/extracted/windows/YUKON.EXE docs/sound-stream-recovery-evidence.json
/Users/miklosme/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  tools/compare_sound_capture.py generated/recovery-proof-sound616/PSND-616.wav \
  local/evidence/blind-playthrough-2026-10-04/02-seattle-to-dyea.avi \
  docs/sound616-capture-comparison.json
python3 -m unittest tests/test_yukonsnd.py -v
```

The comparison uses optional NumPy2.3.5/FFmpeg8.1.2; the decoder and synthetic
tests remain standard-library-only. Four stream names/comments and both slot
bindings are checked by `AnnotateSoundStreams.java`; parameter signatures
remain unchanged. Backup `local/ghidra/backups/sound-stream-before-20261013.tar.gz`.
Use the headless apply/verify commands above with this script and fresh audit
paths. Read-only `sound-memory-stream`, `sound-memory-record`,
`sound-file-stream`, `sound-file-record`, and `sound-header-generic` probes
under `local/ghidra/` reproduce with `DecompileSmoke.java` at the named entries.
**Actual persistence result:** a fresh JVM verified all four names/comments and
both slot bindings; the nine-line apply/reopen audits are byte-identical,
SHA-256 `c714d67b33851c5670757f603897a316b9ee57f1eb14477c9ab4b3e168cc7f21`.

## Bounded clock diagnostic

A follow-up `compare_sound_capture.py ... --diagnose-clock` checks81 uniform
time scales from0.999 to1.001 and41 phases from−1 to+1 comparison samples.
The best fit remains scale1.0/phase−0.3 with correlation0.989638 and14.36%
residual. This excludes an improvement on that tested small clock grid; it does
not explain the remaining mismatch or prove all playback parameters. No source
decoder or playback rate was changed. The grid/result is retained in
`docs/sound616-capture-comparison.json`; use the existing command above with
`--diagnose-clock` to reproduce.

## Selected Linda voices: 22-byte packed headers

This follow-up extends the earlier 54-byte-only bound to the observed **22-byte
header with count 1**, algorithm 3, flags 2. At that checkpoint other sizes/count variants still failed explicitly. The
full-census follow-up below now recovers Linda3402 and all actual source variants.

**Observed source:** NE3:baae reads the header-size word and records the packed
payload start at header start plus that size. It reads packed bits at +4,
expanded bytes at +8, and flags at +3. The flags-2 branch calls NE3:bfd8,
which reads the count word at +12, allocates count × 8 bytes, then copies two
words and one dword per entry from +14 unchanged. Thus the selected 22-byte
header contains one opaque eight-byte entry; the existing 54-byte header
contains five. The meanings of those entry values and seeking behavior remain
unknown. The original constructor does not itself validate algorithm byte +2;
algorithm 3 remains the bounded decoder's explicit supported format guard.
Memory stream slots at NE6:89fc bind reads/cursor changes to NE4:0f4c, 0fd8,
0fa8 and 0fc6.

[Header native evidence](../sound-header-recovery-evidence.json) records original
NE3:baae/bfd8 and memory-stream execution for PSND1,616,3400,3401,3405, with
matching header size, count, copied entry bytes, packed start, block count and
palette. Allocator, OS buffer construction and buffer lock are explicit platform
stubs; count, copy and cursor behavior execute unchanged original instructions.
Source executable/archive hashes are retained in that report.

| PSND | Archive offset | Length | PCM bytes | Native integer calls | PCM SHA-256 |
| --- | --- | --- | --- | --- | --- |
| 3400 | 43210534 | 70557 | 126116 | 1971 | `faef59da722e7f5aa179b655dffc979a00e57a6f257ab713c22aa990dc73ea3a` |
| 3401 | 43413044 | 111046 | 239766 | 3747 | `76c8e6e4caae73eb0d4360e45e657c582956ad854ff25bcbcd8f99684ac7a5aa` |
| 3405 | 43852720 | 79076 | 173403 | 2710 | `ee411d517522b9735467e1b300229f92bc042ddc4bdfd8b43450e8f389255a37` |

[3400](../sound3400-recovery-evidence.json),
[3401](../sound3401-recovery-evidence.json) and
[3405](../sound3405-recovery-evidence.json) retain raw resource hashes, header
bytes, integer/sample counts, final predictor states and zero mismatches against
original NE3:9b34 conversion. For packed inputs larger than a 16-bit segment,
the verifier supplies bounded relocated input windows to the unchanged integer
reader and adjusts the reported cursor origin. This verifies integer decoding
and all samples, **not original huge-buffer allocation or whole playback**.
PSND1 regression still gives the same 81,792 bytes and existing PCM hash.
Synthetic tests retain opaque metadata and reject unsupported count/size pairs.
The earlier PSND616 capture residual remains unexplained and is not superseded
by these exact converter comparisons.

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_sound_header_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/sound-header-recovery-evidence.json
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_sound_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/sound3400-recovery-evidence.json --id 3400
# Repeat the second command with 3401 and 3405 and corresponding report paths.
python3 -m unittest discover -s tests -p 'test_*.py'
```

`AnnotateSound.java` now persists the corrected header consumer comment and
`PackedSound_ReadOpaqueCheckpointPairs` at NE3:bfd8, alongside existing names
and fixed-width structures. Backup:
`local/ghidra/backups/sound-header22-before-20261014.tar.gz`. Apply and fresh-JVM
reopen produced identical 32-record audits, SHA-256
`a671d833ea3c647e30c3956fc149a0ca17772b2e826faab2eba584ab9b68bad3`.
`ProbeSoundHeader.java` exports the stream slot bindings and bounded source
consumers under `local/ghidra/`. Use the existing headless apply/verify commands
with `AnnotateSound.java` to reproduce persistence.

### Selected Linda original-recording comparison

Existing original `local/evidence/seattle-reference-2026-10-13/krnl386_000.avi`
(duration2030.692753s, SHA-256
`f64c3996bcf84bb185ee761ab576ca2d0a0133ca86fdeb65be5d1dbe4ddf8f4d`)
contains both selected Linda lines. A bounded200s PCM clip at original1800s
keeps the existing ten-minute comparison bound; no live UI was controlled.
The sound subagent independently inspected frames at1910/1949s, confirming
Linda with exact TREE3400 override3400/direct-partner response3405 text.
Source record offsets/text bytes and frame hashes are retained in each report.

| Voice | Original alignment seconds | Correlation | Fitted RMS residual | Three consecutive correlations |
| --- | --- | --- | --- | --- |
| 3400 | 1907.56575–1913.2855 | 0.953361 | 30.183% | 0.955211 / 0.936954 / 0.965136 |
| 3405 | 1945.08925–1952.9535 | 0.972743 | 23.189% | 0.965248 / 0.978858 / 0.969917 |

[3400 comparison](../sound3400-capture-comparison.json) and
[3405 comparison](../sound3405-capture-comparison.json) retain gain/DC and every
third's residual. Separate within-one-sample phase refinement improves3400 to
0.993021/11.794% residual and3405 to0.989382/14.534%; no time stretch or source
playback parameter was changed. The **unrefined residuals remain unexplained**,
including original mixer/filter/resampling effects. Exact native converter
agreement and strong captured waveform/text correspondence establish only
these selected resource mappings, not whole audio fidelity or bit-identical
capture PCM. The fitted gains are measurements, not proposed volume settings.

```sh
python3 tools/yukonsnd.py original/extracted/windows/YUKONRES \
  generated/linda-audio-comparison-20261014 --id 3400
python3 tools/yukonsnd.py original/extracted/windows/YUKONRES \
  generated/linda-audio-comparison-20261014 --id 3405
ffmpeg -nostdin -v error -ss 1800 \
  -i local/evidence/seattle-reference-2026-10-13/krnl386_000.avi \
  -t 200 -vn -c:a pcm_s16le \
  local/evidence/recovery-proof/linda-capture-1800-2000-20261014.wav
/Users/miklosme/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  tools/compare_sound_capture.py generated/linda-audio-comparison-20261014/PSND-3400.wav \
  local/evidence/recovery-proof/linda-capture-1800-2000-20261014.wav \
  docs/sound3400-capture-comparison.json
# Repeat comparison with3405. Reports additionally retain original clip offset,
# original AVI identity, frame identity and observed source text corroboration.
ffmpeg -nostdin -v error -ss 1910 \
  -i local/evidence/seattle-reference-2026-10-13/krnl386_000.avi -frames:v 1 \
  local/evidence/recovery-proof/linda-3400-1910s-20261014.png
# Repeat frame extraction at1949s with the3405 frame path.
```

Analysis uses optional NumPy2.3.5/FFmpeg8.1.2. Source/WAV/PCM/clip hashes are
retained; all media and extracted frames remain ignored local artifacts.


## Complete actual census and bounded sequential extension

[audit_sounds.py](../../tools/audit_sounds.py) inventories all871 actual PSND
records, preserving every resource ID/offset/length/hash, parameter/header/count
variant, decoder status and PCM hash. [Before-extension census](../sound-census-before-extension.json)
records162 accepted/709 rejected and its exact decoder source hash.
[Final census](../sound-census-evidence.json) records **871 accepted, zero rejected**
and the new decoder hash. This is decoder acceptance coverage, not complete
native playback or audio fidelity. All records are mono8-bit/rate22/algorithm3;
43 parameter combinations remain separately listed. Headers:168 flags0/size12
records with no checkpoint count, and703 flags2 records with size14+8×count.
Actual indexed counts are1–22 or26. Orders:783 order2,75 order1,11 order3,
one order4 andone order0.

[Header native proof](../sound-header-recovery-evidence.json) executes original
NE3:baae/bfd8 and NE4 memory-stream methods for all871 actual headers plus27
synthetic cases (positive counts1–26, flags0/header12). Count/copy/cursor,
expanded size, ceil64 blocks and palette match. Platform allocation/buffer
construction/lock remain explicit stubs. The decoder requires flags0 exactly
size12 or flags2 exactlysize14+8×positive count1–26; it does not accept arbitrary
sizes. Pair meanings, seeking and looping remain unknown. The synthetic54-byte
fixture now has actual count5+40 opaque bytes; its earlier all-zero42-byte
metadata encoded count0, not an actual source variant.

### Declared bits and original stopping behavior

Nine source records invalidated the earlier exact declared-bit bound:
1302,2105,3402,395,4123,4452,630,638,8114. Original NE3:be0e bounds actual stream
bytes and remaining blocks; NE3:bbee clamps output at expanded bytes. Neither
terminal path requires exact consumption of field580. PSND395's declared field
exceeds physical input by10 bits, while its required final block stays within
physical bytes.

[Terminal native proof](../sound-terminal-recovery-evidence.json) executes
original **be0e final-block loop,63fe whole64-byte decoder and NE1 bit helpers**
for allnine cases:64 bytes, bitcursor, original memory-stream cursor/window,
remaining blocks and emitted count match. Input is an explicitly relocated
bounded suffix; these final blocks have no reference/repeat. Header allocation
stubs are unchanged; no terminal block/cursor/count behavior is stubbed. Whole
processor/Win16 huge-buffer allocation/mixer remain excluded. Source exports:
`local/ghidra/sound-decode-blocks.asm.txt`, `sound-block-output.asm.txt`, and
`sound-block-63fe.asm.txt` (the last supplied by the independent image worker).

The decoder bounds reads by physical bytes and requires **0–7 unused physical
bits** after the expanded ceil64 blocks. Declared bits, consumed bits, terminal
unused count/value and final partial-block bytes are retained separately. An
extra encoded block or trailing byte still fails. Source control flow explains
why declared bits need not equal consumption; why the encoder wrote these
particular differing declared values remains unknown. No invented correction
to that metadata determines PCM.

Original NE3:9b34 order0 returns bytes/state unchanged; orders1–4 retain the
recovered wrapping integration. [Rare-order proof](../sound-orders-recovery-evidence.json)
compares every13 actual order0/3/4 record's original integer reads, samples and
final state before enabling those orders. Rate/channel/depth guards remain
unchanged; unsupported future formats still fail.

### Selected Seattle voices and actual exported WAVs

[Seattle native set](../seattle-sound-set-recovery-evidence.json) derives voice
IDs from actual normalized TREE1,600,2100,3100,3200,3300,3400, preserving voiced
record offsets/text hashes. **47 mapped voices,119,127 original integer reads
and7,626,207 sample bytes** match original code, including final states.
TREE IDs are not assumed to equal voice IDs. Linda3402 has actualheader30/count2
(the earlier38/count3 lead was incorrect);3404 and unindexed3406 also pass.
Voice/graph import coverage does not establish UI/actions/conditions.

A fresh existing `prepare_browser_assets.py` export into
`generated/seattle-sound-export-20261014` passed
[47 actual WAV comparisons](../seattle-sound-export-evidence.json): WAV hashes,
mono8-bit/22050 parameters, raw identities and PCM match the independent native
oracle. [verify_prepared_sound_assets.py](../../tools/verify_prepared_sound_assets.py)
reproduces that check. Served packages were not replaced, and this is not a
browser output test. Add the same sound IDs to a future full scene package;
the report is the source-mapped manifest.

```sh
python3 tools/audit_sounds.py original/extracted/windows/YUKONRES docs/sound-census-evidence.json
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_sound_header_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE docs/sound-header-recovery-evidence.json
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_sound_terminal_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE docs/sound-terminal-recovery-evidence.json
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_sound_orders_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE docs/sound-orders-recovery-evidence.json
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_seattle_sound_set_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE docs/seattle-sound-set-recovery-evidence.json
```

Fresh preparation (choose a new ignored output each run; bitmap1/font/palette
satisfy the importer contract, without a new image/font fidelity claim):

```sh
python3 - <<'PY'
import json, subprocess
proof = json.load(open('docs/seattle-sound-set-recovery-evidence.json'))
args = ['python3', 'tools/prepare_browser_assets.py',
        'original/extracted/windows/YUKONRES', 'original/extracted/windows/YUKON.EXE',
        'original/extracted/windows/YUF_____.TTF', 'generated/seattle-sound-export-20261014',
        '--bitmap', '1', '--system-palette-zero-rgb', '0,0,0']
for key in proof['trees']:
    args += ['--tree', key.split(':')[1]]
for key in proof['sounds']:
    args += ['--sound', key.split(':')[1]]
subprocess.run(args, check=True)
PY
python3 tools/verify_prepared_sound_assets.py generated/seattle-sound-export-20261014 \
  docs/seattle-sound-set-recovery-evidence.json docs/seattle-sound-export-evidence.json
python3 -m unittest tests.test_yukonsnd tests.test_audit_sounds
```

`AnnotateSound.java` persists12 functions plus existing fixed-width structures,
including63fe/be0e/bbee and corrected header/order comments. Backup:
`local/ghidra/backups/sound-census-before-20261014.tar.gz`. Fresh-JVM apply/reopen
contains36 identical audit records, SHA-256 `4d77424389fab7ec3fd8c14aaf524bfcd73b61444ec4c16e85efb5e12a46c820`.
No guessed signatures, playback volume/timing or original media changes.

### Naturally reached Linda insufficient-funds voice

TREE600, offset0x534005d,length1648,SHA-256
`d3be3d9e229d178ba265ee91e7d5057ee343526a8a2f95c63227b17323d289aa`,
has no initial overrides. Root+0x116 has **voice601 at+0x126**, text+0x128:
`We don't have enough money for that.` PSND600 and MidasPSND1 are not that voice.
[PSND601 native proof](../sound601-recovery-evidence.json) checks591 reads and
37,824 samples, PCM SHA-256
`da40d6eb457bc0974b68eaa9df2ae64ebb7df2e651e2d920ae24a5c0246c3fc9`.

The independent original worker naturally reached this refusal while selecting
1,600lb food for$240 with$222 in White Pass City. Final006AVI SHA-256
`5e593e634b43c8eb0f9096ab2c18d8dad962ee5652f46fe0f0b2a3718e2e6562`,
duration789.090896s, contains the voice at **667.10025–668.81575s**.
A bounded100s audio clip from640s yields correlation**0.995244**, fitted RMS
residual**9.741%**; thirds0.994400/0.996584/0.992733 agree. Separate phase−0.15
sample refinement gives0.998180/6.030% residual, with no stretching or changed
playback. The sound worker independently inspected the668s frame: Linda and
exact source text visible. [Capture report](../sound601-capture-comparison.json)
retains AVI/clip/WAV/frame/TREE hashes and each metric. Residual remains
unexplained; selected agreement is not bit-identical/mixer/overall fidelity.
No live GUI action was used for this comparison.

```sh
python3 tools/yukonsnd.py original/extracted/windows/YUKONRES generated/linda-refusal-audio-20261014 --id 601
ffmpeg -nostdin -v error -ss 640 -i local/evidence/seattle-reference-2026-10-13/krnl386_006.avi \
  -t 100 -vn -c:a pcm_s16le local/evidence/recovery-proof/linda-refusal-capture-640-740-20261014.wav
/Users/miklosme/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  tools/compare_sound_capture.py generated/linda-refusal-audio-20261014/PSND-601.wav \
  local/evidence/recovery-proof/linda-refusal-capture-640-740-20261014.wav docs/sound601-capture-comparison.json
```

Final verification: all871 census PCM hashes are retained; each of the47
selected Seattle census hashes also matches its original-code oracle. Full
standard-library suite174 passes, decoder/verifier compilation and diff checks
are clean. Optional native proofs use pinned Unicorn2.1.4; no runtime dependency
was added.
