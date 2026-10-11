# Audio evidence and unresolved playback paths

Inspection: 2026-10-04. This is a read-only source inspection, not an audio
decoder or a playback verification. All executable addresses use the mapping
from [the saved NE import](ANALYSIS.md). A later reference setup ran the
original opening and captured nonzero emulator PCM output; see
[REFERENCE.md](REFERENCE.md). That runtime check does not identify individual
PSND resources, establish their source parameters, or settle audio completeness.

## Source identities

| Local source | Size | SHA-256 |
| --- | ---: | --- |
| `original/extracted/windows/README.TXT` | 5,435 | `06349946597598f5eb66d1a54d1a44e480b1e56f3c2775c6a4d252577861feb2` |
| `original/extracted/windows/YUKONCD.INF` | 16,285 | `5717b561682bb430e5ca3dae3f6440e8710a2ea5af033c0c39e66ba67cdcd1ab` |
| `original/extracted/windows/YUKON.EXE` | 404,272 | `9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06` |
| `original/extracted/windows/YUKONRES` | 87,911,322 | `438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6` |

The README, installer, executable, and raw sound export hashes were rechecked
locally against the existing metadata. The archive identity and the export's
byte-preserving verification are recorded in [the index specification](formats/YUKONRES.md).

## Observed disc and installation text

**Observed, README file offsets `0xa6e`–`0xb6f`:** the bonus section describes
music that can be played using a CD-ROM drive or an audio CD player. It assigns
computer data to track 1 and tells audio-player users to start at track 2.
The list runs from track 2 (`0xba3`) through track 18 (`0x10c5`). This text
describes the original disc; it does not establish the downloaded image's
physical track inventory or the game's playback mechanism.

**Observed, README offsets `0xe54`–`0xef3`:** track 11 is identified as the dog
sled race theme, and the accompanying text says that this music was not
included in the CD-ROM version of the game. Consequently, the list of bonus
tracks cannot itself be treated as a list of required in-game audio.

**Observed, installer text beginning at file offset `0x22f8`:** the installer asks
whether a Windows-compatible sound card is available. The following branch
writes the separate `Allow music`, `Allow sound`, and `Allow voice` keys under
`Game Configuration`: all three receive `1` for Yes and `0` for No. Key text
starts at `0x25a8`, `0x265f`, `0x2716` in the Yes branch and `0x27d4`,
`0x288b`, `0x2942` in the No branch. This establishes installer settings;
it does not establish which resource or device each setting controls.

## Observed executable leads

These are null-terminated byte strings in initialized `Data13`. For each,
the NE offset is the original file offset minus the segment's file start
`0x4f420`; Ghidra maps NE segment `000d` to selector `1060`.

| Text | Original file offset | NE segment:offset | Ghidra mapping |
| --- | --- | --- | --- |
| `MECCSndClass` | `0x507d8` | `000d:13b8` | `1060:13b8` |
| `%u.wav` | `0x507ff` | `000d:13df` | `1060:13df` |
| `waveaudio` | `0x50806` | `000d:13e6` | `1060:13e6` |
| `%u.mid` | `0x50810` | `000d:13f0` | `1060:13f0` |
| `sequencer` | `0x50817` | `000d:13f7` | `1060:13f7` |
| `%u.pak` | `0x5373a` | `000d:431a` | `1060:431a` |
| `%u.wav` | `0x53742` | `000d:4322` | `1060:4322` |
| `WAVE` | `0x5374d` | `000d:432d` | `1060:432d` |
| `MECCMixedSndSrvrClass` | `0x53752` | `000d:4332` | `1060:4332` |

**Observed tool output:** the existing saved import audit identifies
`MMSYSTEM::MCISENDCOMMAND`, `TIMEGETTIME`, and these eight waveform output
imports: `WAVEOUTOPEN`, `WAVEOUTCLOSE`, `WAVEOUTPREPAREHEADER`,
`WAVEOUTUNPREPAREHEADER`, `WAVEOUTWRITE`, `WAVEOUTRESET`,
`WAVEOUTGETPOSITION`, and `WAVEOUTSETVOLUME`.
The local artifact is `local/ghidra/leads-audit.tsv`, SHA-256
`b4e1eecf3bdb6733616ce895200004312a1ebc35d1c66e323e3625392b3656e2`.
These are imported API names resolved by Ghidra's Win16 export table, not
validated parameter types.

**Inferred leads:** the adjacent filename/device strings suggest waveform
and sequencer paths worth tracing. Microsoft documents `waveaudio` and
`sequencer` as MCI compound device types, while `cdaudio` is a simple device.
That distinction supports the next investigation, not a claim that these
strings are used or that CD audio is unused. See Microsoft's
[MCI device-opening documentation](https://learn.microsoft.com/en-us/windows/win32/multimedia/opening-a-device).
Its current Win32 declarations must not be substituted for this executable's
Win16 structures and calling conventions without checking historical headers
and actual disassembly.

**Observed disassembly follow-up:** the archive-consumer investigation's
read-only export `local/ghidra/archive-trace.asm.tsv` contains two parallel
sequences. Their six nonrelocated source instructions below were independently
checked against the original executable bytes; each agrees with the export.
This export has SHA-256
`44eafeaaec3a17b6e64be2905eb72ada2aeb7020c00386198b7310f645f19cb0`.

| NE segment:offset | Ghidra mapping | Original file offset | Source bytes | Exported instruction |
| --- | --- | --- | --- | --- |
| `0003:90ac` | `1010:90ac` | `0x26e8c` | `68 df 13` | `PUSH 0x13df` |
| `0003:90bc` | `1010:90bc` | `0x26e9c` | `c7 46 f4 e6 13` | `MOV word ptr [BP - 0xc],0x13e6` |
| `0003:90c1` | `1010:90c1` | `0x26ea1` | `8c 5e f6` | `MOV word ptr [BP - 0xa],DS` |
| `0003:921a` | `1010:921a` | `0x26ffa` | `68 f0 13` | `PUSH 0x13f0` |
| `0003:922a` | `1010:922a` | `0x2700a` | `c7 46 f4 f7 13` | `MOV word ptr [BP - 0xc],0x13f7` |
| `0003:922f` | `1010:922f` | `0x2700f` | `8c 5e f6` | `MOV word ptr [BP - 0xa],DS` |

The first sequence is in the function currently beginning at NE `0003:9000`
/ Ghidra `1010:9000`; the second is in NE `0003:916e` / Ghidra `1010:916e`.
Each pushes `DS` immediately before the filename-pattern offset, calls the
same relocated thunk `11c8:02ac`, constructs a far pointer using the following
device-name offset and `DS`, and calls relocated thunk `11c8:02e8`.
These offsets match the waveform and sequencer string pairs above. They are
concrete consumer leads; incoming `DS`, thunk identity, Win16 parameter-block
layout, callers, and the selected element's origin still need verification
before assigning this path to a particular game resource or setting.

## Observed selected archive bytes

`PSND:1` has index entry offset `0x31d6`, archive payload offset `0xbe2a4d`,
and byte length 45,300. The existing raw export is
`generated/yukonres-index/PSND-1.bin`, SHA-256
`a671dfae45ada8f46ea6a9d8ce0042d53234106ec6c479e60590ca8f55b1fa40`.
Its first sixteen bytes are:

```text
01 81 0c 00 00 00 01 08 16 01 02 19 02 80 32 00
```

Those bytes do not begin with `RIFF`. This is a byte observation, not evidence
for a particular compression, sample rate, channel count, byte order, or
internal header layout. Neither the `PSND` type name nor the nearby executable
`WAVE` string establishes this record's playback format.

## Reproduction and next consumer question

Use Python 3.14.5 or the tools already documented in the repository. From the
repository root:

```sh
shasum -a 256 original/extracted/windows/README.TXT \
  original/extracted/windows/YUKONCD.INF original/extracted/windows/YUKON.EXE \
  generated/yukonres-index/PSND-1.bin
rg -a -n -i 'track|audio|music' original/extracted/windows/README.TXT
rg -n -i 'sound|voice|music' original/extracted/windows/YUKONCD.INF
rg 'MMSYSTEM::' local/ghidra/leads-audit.tsv
xxd -l 16 generated/yukonres-index/PSND-1.bin
```

Reproduce exact byte offsets and address mappings without opening the project:

```sh
python3 - <<'PY'
from pathlib import Path
d = Path('original/extracted/windows/YUKON.EXE').read_bytes()
for offset in (0x507d8, 0x507ff, 0x50806, 0x50810, 0x50817,
               0x5373a, 0x53742, 0x5374d, 0x53752):
    text = d[offset:d.index(0, offset)].decode('ascii')
    relative = offset - 0x4f420
    print(f'{offset:#x} NE 000d:{relative:04x} Ghidra 1060:{relative:04x} {text}')
for offset, size in ((0x90ac, 3), (0x90bc, 5), (0x90c1, 3),
                     (0x921a, 3), (0x922a, 5), (0x922f, 3)):
    file_offset = 0x1dde0 + offset
    print(f'NE 0003:{offset:04x} Ghidra 1010:{offset:04x} '
          f'file {file_offset:#x}: {d[file_offset:file_offset + size].hex(" ")}')
PY
```

**Next concrete question:** verify the incoming data segment, API thunks, and
Win16 open parameter block of NE `0003:9000` and `0003:916e`, then follow
their callers and filename element's origin before assigning a resource type
to music. Separately trace the
`WAVEOUTOPEN` format pointer and `WAVEOUTWRITE` buffer back to a selected
`PSND` lookup, checking segmented pointers and any conversion function.

**Unknown:** the original interaction using `PSND:1`, broader sound formats, which resource holds music,
whether any in-game path requests CD-DA, and whether the downloaded ISO is
sufficient for all in-game audio. Original-versus-recovered playback checks
remain necessary. This investigation does not establish that game music is
missing.

## Selected PSND record and consumer follow-up

**Observed, 2026-10-04:** CBMP and PSND have no pattern in the17 observed
startup postread registrations; see [ARCHIVE-CONSUMERS.md](ARCHIVE-CONSUMERS.md).
The file-slice branch passes through NE `0005:8bd6` / Ghidra `1020:8bd6`;
the buffer constructor `0004:0ef0` / `1018:0ef0` builds a memory stream,
rather than itself decoding sound. NE `0003:acea` / `1010:acea` constructs
the sound processor, reading records through its stream method slot `+18`.
Code3's source file base is `0x1dde0`; Code4's is `0x2cac0`, Code5's `0x3b800`.
All refer to the source EXE hash above; default decompiler signatures remain
unverified.

For PSND1 (archive `0xbe2a4d`, 45,300 bytes), raw record observations are:

| Payload offset | Type byte | Byte1 | Little-endian record length at+2 | Evidence |
| --- | ---: | ---: | ---: | --- |
| `0` | 1 | `0x81` | 12 | Header bytes `01 81 0c 00 00 00 01 08 16 01 02 19` |
| `0x0c` | 2 | `0x80` | 50 | Consumer handles type 2 through `0003:b3a2`; metadata meaning incomplete |
| `0x3e` | 0 | `0x80` | 6 | Compressed data follows at `0x44` |

The chunk at `0x44` has header size 54, algorithm3, flags2, packed bit
count 361,423, expanded size 81,792. It shares some integer primitives with
images but is **not** supported by the flags1 image decoder. No PCM semantics
are assigned merely from these bytes.

**Observed:** `0003:acea` copies header bytes6/7/8/10 into object words
`+1c/+1e/+20/+1a`, and initializes object dword `+2c` to `0x80808080`.
Packed-stream constructor `0003:b636` calls header reader `0003:baae`, which
reads expanded size, bit count and flags, invokes `0003:bfd8` for flags bit 1,
and initializes a256-entry table `128,127,129,126,130,125,…`.
This is a conversion lead, not yet a verified predictor/delta format.
Reader `0003:bbee` handles partial64-byte blocks and calls `0003:be0e` for
whole blocks. The processor then invokes `0003:9b34` at `b030`, supplying the
header-derived word `+1a` and state pointer `+2c`; its sequential conversion is
now recovered below.

Read-only API-thunk export finds WAVEOUTOPEN callers at `0003:9826` and
`0003:9f0f` (Ghidra `1010:9826/9f0f`). The first supplies a format at object
`+44`; constructor `0003:92dc` builds it. At `94bf–94ed`, a virtual getter's
result 11 maps to 11,025 and22 maps to 22,050; `94f5` writes format word 1,
`950e` writes a getter result to channels at `+46`, `9516` writes rate at
`+48`, and `958e` writes bit depth at `+52`. The subsequent getter-binding and
converter recovery establishes selected PSND1 parameters in
[formats/PSND.md](formats/PSND.md). Other branches remain unvalidated.

These probes are in ignored `local/ghidra/recovery-psnd-parse`,
`recovery-audio-next-block`, `recovery-audio-block`, and `recovery-wave-open`
(`.c` and `.asm.txt`). Reproduce with `DecompileSmoke.java` at `1010:acea`,
`1010:baae`, `1010:bbee`, and `1010:978a`, using the read-only headless command
in [formats/CBMP.md](formats/CBMP.md). Use assembly rather than guessed C types.
API callers reproduce with `ExportResourceAPIs.java output.tsv`.

**Observed follow-up:** selected PSND1 expands to 81,792 mono 8-bit 22,050 Hz
samples with second-order integration. All 1,278 integer calls and all converted
samples/final state match original-code execution; supported names, getter
bindings and an observed header layout persist in Ghidra. This is sequential
source decoding, not an individual-PSND live playback comparison.
[formats/PSND.md](formats/PSND.md) and
[sound-recovery-evidence.json](sound-recovery-evidence.json) contain the results.

**Next concrete action:** trace PSND1's dialogue/scene use and compare a deliberately
captured original clip. Existing opening captures produced no convincing
waveform match. Loop/seek semantics, broader parameters and resource-to-scene
mapping remain unknown; M1 remains incomplete.
