# Bounded sequential PSND1 recovery

Checked 2026-10-04. **Observed:** PSND1 expands to 81,792 unsigned 8-bit mono
samples at 22,050 Hz (about 3.7094 seconds). All 1,278 integer-reader calls and
all sample conversions agree with execution of the original x86 routines.
The source format and getter bindings establish the playback parameters.
**Unknown:** the original interaction that plays this resource. No live
resource-mapped playback comparison is claimed. Seeking, looping, other sample
parameters and other resources remain unsupported by this proof tool.

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
