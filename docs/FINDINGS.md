# Source and binary findings

Inspection date: 2026-10-04. These findings refer to the exact source hashes in [the manifest](source-manifest.json), not every edition of The Yukon Trail.

Use **observed** for bytes, file metadata, or behavior directly checked; **inferred** for interpretations supported by that evidence; **unknown** for unfinished investigation. The archive index is a checked structural interpretation, not a complete format specification.

## Disc and provenance

**Observed:** `original/iso/YUKONCD.ISO` is 370,939,904 bytes (about 354 MiB). Its ISO9660 volume label is `YUKONCD`. `bsdtar` can list and extract the Windows-visible files. An Apple partition map contains an `Apple_HFS` partition starting at block `0x5b142`, with length `0x55810` in 512-byte blocks. At partition start plus 1,024 bytes, the HFS master directory block has signature `BD` and volume name `Yukon Trail`.

**Observed in the follow-up inventory:** the classic HFS catalog contains 170
files and 24 folders including the root. Ninety-nine files have nonempty resource
forks. The Mac `YUKONRES` data fork (CNID 185, inline extent `(721, 21463)`,
absolute ISO offset `0xb8fb000`, length 87,911,322) has the same SHA-256 as the
Windows archive. The Mac application has distinct data and resource forks.
See [the bounded read-only inventory and exact evidence](MAC-SOURCE.md).
No Mac forks have been extracted and no Mac game has run.

**Observed in source verification:** the owner supplied
`https://archive.org/details/YUKONCD`. The local ISO matches the item entry's
size, MD5, SHA-1 and CRC32, and its recorded SHA-256 is unchanged. JSON and XML
file lists agree on eight files, including one ISO and no separate CUE/BIN,
audio tracks or Windows installation media. The source provenance and snapshot
hashes are recorded in [SOURCE-PROVENANCE.md](SOURCE-PROVENANCE.md).

**Unknown:** behavioral/platform differences between the executables, successful
fork restoration, and completeness relative to a physical original disc. The
owner's download date is still unknown; the Archive added date is not a download
date.

The local `hdiutil imageinfo` attempt failed with “Device not configured.” That did not prevent ISO9660 reads through `bsdtar`; it is not evidence that the image is corrupt.

## Windows-visible files

| File/path | Observed size or contents | Relevance |
| --- | --- | --- |
| `YUKON.EXE` | 404,272 bytes; `NE` signature at file offset `0x80`; version 1.1 text | Native Windows 3.x program to analyze |
| `YUKONRES` | 87,911,322 bytes; MECC/title/version header | Main custom resource archive |
| `YUKONCD.INF` | 16,285 bytes; readable installer instructions | Installation, font, INI keys, display requirements |
| `YUKHELP.HLP` | 63,889 bytes | Original help; not decoded yet |
| `YUF_____.TTF` | 24,236 bytes | Original TrueType font |
| `YLOGO.BMP` | 81,958 bytes; 352 × 230, 8-bit BMP | Standard-format installer artwork |
| `READINGS/` | Eight files: CLANCY, CREDITS, CREMATE, HARDLUCK, HOUSEKP, TOBUILD, TRAIL98, YUKONSP | Embedded reading/credit material |
| `README.TXT` | 5,435 bytes | Disc/platform information and audio-track list |
| `DOSDEMO/`, `WINDEMO/` | Multiple separate products and a Yukon demo | Possible comparison material; keep separate from full game |
| `AOL/` and registration/setup utilities | Bundled unrelated software | Outside the port’s scope |

**Observed:** the executable imports `KERNEL`, `GDI`, `USER`, `WIN87EM`,
`COMMDLG`, and `MMSYSTEM`. The raw NE import-table follow-up identified `GDI`,
omitted from the initial notes. Strings include wave/MIDI filename patterns and
`waveaudio`. Readable material covers travel, inventory, health, events,
dialogue, and claims. Persistent-analysis setup and mapping evidence are recorded
in [ANALYSIS.md](ANALYSIS.md).

**Inferred:** the port will need native-code analysis as well as resource extraction. No source project was found in the inspected Windows tree. These findings do not establish the original language/compiler or eliminate the possibility of data-driven gameplay.

The installer checks for at least 640 × 480 display dimensions, 256 colors, and Windows 3.1. These are installation requirements, **not a verified game viewport size**. It names `YUKON.INI`, the game font, and separate music/sound/voice settings.

## YUKONRES index

The following interpretation was checked against the entire index. Offsets are hexadecimal file offsets; integers in these tables are **big-endian**. Do not apply that byte order to payloads without further evidence.

| Offset | Length | Observation / interpretation |
| --- | --- | --- |
| `0x00` | 4 | Bytes `00 58 8a 94`; meaning unknown |
| `0x04` | 4 | ASCII `MECC` |
| `0x0a` | — | Null-terminated `Yukon Trail` text; surrounding field layout unproven |
| `0x4a` | — | `1.1` text; surrounding field layout unproven |
| `0x54` | 2 | Type-group count: 21 |
| `0x56` | 2 | Record count: 2,522 (`0x09da`) |
| `0x58` | 21 × 8 | Group table: tag (4 bytes), count (u16), first record index (u16) |
| `0x100` | 2,522 × 14 | Resource index; ends at `0x8aec` exclusive |

Each 14-byte resource entry:

| Relative offset | Length | Interpretation |
| --- | --- | --- |
| `+0` | 4 | ASCII type tag |
| `+4` | 2 | Resource ID, u16 |
| `+6` | 4 | Payload byte length, u32 |
| `+10` | 4 | Absolute payload file offset, u32 |

Validation performed: all payload intervals begin at or after the index end and
end within the archive; every `(tag, ID)` pair is unique; each group's indicated
slice contains its advertised tag; record counts sum to 2,522. The reusable
reader subsequently confirmed contiguous group coverage and no overlapping
positive-length payloads. `TREE:39` (index entry `0x7058`) has length zero and
payload offset `0x52a96df`; its meaning remains unknown.

The [format specification and reader verification](formats/YUKONRES.md) record
23 synthetic tests and byte-preserving exports of five independently located
records. These checks establish index parsing and raw export, not payload
semantics or support for other editions.

**Observed static consumer evidence:** NE `0001:73fa` (Ghidra `1000:73fa`,
source offset `0x785a`) reads a `0x58` header, group-count × 8 bytes and
record-count × 14 bytes, then swaps the same numeric fields. NE `0001:75fe`
(`1000:75fe`, source `0x7a5e`) searches raw tags and unsigned 16-bit IDs;
counts/bounds use signed 16-bit operations. Its disassembly-derived search
matches all 2,522 physical source ordinals and 43 absent-key checks. NE
`0001:7818` reads the selected payload using entry `+0a` as absolute offset and
`+06` as length, then calls unresolved `0001:8462`. A raw export is therefore
not yet established as the final image/audio consumer buffer. Details, source
hashes, callers, saved types/names and reopen checks are in
[ARCHIVE-CONSUMERS.md](ARCHIVE-CONSUMERS.md).

| Type | Count | Type | Count | Type | Count |
| --- | ---: | --- | ---: | --- | ---: |
| ACEL | 173 | ASEQ | 159 | BLCK | 2 |
| CBMP | 331 | CLMN | 1 | CMIN | 40 |
| CONV | 137 | CSTR | 15 | FMAP | 2 |
| FNTL | 2 | HSPT | 31 | PSND | 871 |
| RLEA | 18 | SCNE | 30 | SCRP | 34 |
| SMAP | 2 | SNDQ | 21 | SPRT | 140 |
| TREE | 510 | VERS | 1 | WRLD | 2 |

Sample records located through the index:

| Key | Payload offset | Byte length | Direct observation |
| --- | --- | ---: | --- |
| `CSTR:500` | `0xbdfd55` | 2,302 | Readable advisor/journal text after initial binary bytes |
| `SCRP:1000` | `0x51be0cd` | 164 | Structured binary data, not high-level source text |
| `CBMP:1` | `0x74dd6` | 1,842 | Nonstandard binary payload; image decoding not implemented |
| `PSND:1` | `0xbe2a4d` | 45,300 | Nonstandard binary payload; sound decoding not implemented |

Names such as `CBMP`, `PSND`, `SCNE`, and `SCRP` suggest images, sound, scenes, and scripts. Those meanings and any cross-resource relationships must be established by tracing consumers in the executable. We have not recovered compression, palettes, sample rates, bytecode instructions, or a scene graph.

## Audio completeness

**Observed:** the disc README describes bonus music playable from tracks 2–18, with track 1 holding computer data. The inspected source is one ISO file. It also explicitly describes one track as music that did not appear in the CD-ROM game.

**Observed:** the supplied Archive item currently lists no separate audio files
or CUE/BIN. This settles that item's public file inventory only. The executable
contains waveform/sequencer filename and MCI device strings and imports MCI and
waveform output APIs; exact identities, offsets and limits are in
[AUDIO-EVIDENCE.md](AUDIO-EVIDENCE.md).

**Unknown:** whether any game path uses CD-DA and which resources contain music.
Do not report game music as missing based on the ISO extension or bonus-track
list. Trace the original MCI/waveout callers and validate playback in the original.

## Observed original opening

**Observed on 2026-10-04:** the verified full-game `YUKON.EXE` (SHA-256
`9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`)
runs unmodified in DOSBox-X 2026.10.01 with Windows Version 3.10 in 386 Enhanced
Mode. The installed copy matches the disc; resources remain on the mounted,
unchanged ISO. The reconstructed system/driver configuration is recorded in
[REFERENCE.md](REFERENCE.md).

After entering `reference` in the name dialog, the opening journal displays
August 23, 1897, arrival in Seattle, 0 pounds of food and $350 cash. Evidence:
native `local/evidence/reference/krnl386_002.png`, 147,863 bytes, SHA-256
`5c91d7eb9f4841f84708f8a7dff61d3324e52bdeda2392b25542a2da06785fe3`.
The first-launch AVI passes full FFmpeg decode; the separate WAV has nonzero
emulator PCM output. These record the observed opening, not recovered asset
formats or a port comparison. Capture output rates are not PSND source rates.

**Unknown at the opening checkpoint:** broader interaction/progression, other
paths, and audio completeness. The later blind run below adds one observed path.
The standard Windows mouse driver exposed a host/guest pointer mismatch in UI
automation; the official DOSBox-X Win31 integration driver fixes it as a
reference-platform input configuration, without changing the game executable.
A fresh emulator process repeated the name/journal sequence, and Done dismissed
the journal to Seattle Wharf. Native scene evidence:
`local/evidence/reference/krnl386_006.png`, 204,053 bytes, SHA-256
`01ace7b331d5d32f43b12d79fea88adcb4d8ca68d58817638d72a06fc60864eb`.
No purchases, travel, save/load or playthrough were performed during setup.

## Observed blind original-game ending

**Observed on 2026-10-04:** a fresh subagent run named `blind` used the same
unmodified executable and reference configuration, with no walkthrough or
recovered-behavior guidance. It completed Seattle preparation, the Yosemite
voyage to Dyea, Chilkoot travel with a customs turnback for food, boat building
at Lake Bennett, three rafting courses, Dawson prospecting, and mining on No. 5
Below Bonanza Creek. The agent then followed the game's winter instructions to
cash in and head home. One ordinary save was made; none was loaded.

The game displayed a congratulatory dialogue, then the newspaper headline
“Klondike Pair Reaches Dawson / They Find Enough Gold to Pay for Passage Home.”
Root independently inspected the native PNGs:

- `local/evidence/blind-playthrough-2026-10-04/12-ending-dialogue.png`:
  155,767 bytes; SHA-256
  `5817f35362f2ddced25f9ec93952c9a11ac89a587a9c4945b1c682baa605c6ec`.
- `local/evidence/blind-playthrough-2026-10-04/13-ending-newspaper.png`:
  207,317 bytes; SHA-256
  `cecde54131ce2d57d0985d6b9ba0e7b8e293d16558fb6ad017ec97fc29bfacb7`.
- `local/evidence/blind-playthrough-2026-10-04/14-final-score.png`:
  151,678 bytes; SHA-256
  `dc29799f288ab9e3a2afd3a121ca348003884bdeb084978f0fdd5b7a5e75c902`.
  Displays `blind`, `Stampeder`, `14586`, `Jul 6, 1898`.
- `local/evidence/blind-playthrough-2026-10-04/15-new-run-prompt.png`:
  164,977 bytes; SHA-256
  `1c3b5764d02734b0787a1f23da9de66d906103986d1f1fd39661933207662282`.
  After Claims of Fame Done, displays fresh name entry at Seattle Wharf.

[BLIND-PLAYTHROUGH.md](BLIND-PLAYTHROUGH.md) records the detailed choices,
Claims of Fame result, capture identities, and continuation check. The ISO,
resource archive, installed executable, and configuration still match the
recorded SHA-256 identities. All three voyage, White Horse rafting, and
mining/ending AVIs passed
full FFmpeg decode; independent sample-frame checks are scoped separately from
the agent's live observations.

**Unknown:** alternative routes/partners/claims/endings, exact random seeds,
timing and collision causes, and save/load correctness. This one finished
original run does not establish a recovered rule model or port fidelity.

## Selected image recovery

**Observed:** the original CBMP consumers expose little-endian frame records
and algorithm3 packed blocks, using MSB-first integers and8×8 column-major
tiles. An embedded executable palette is loaded by NE `0001:5eb4` from custom
type 2000/ID100 at file `0x618e0`. Both CBMP1 and CBMP2 decode to 557×117 and
consume their exact declared bit/expanded lengths. All 679 integer-reader calls
match original NE `0001:0062/0129` output bytes and returned cursor.
CBMP2's6,230 border pixels match the native ending dialogue at `(50,234)`
after the explicit palette conversion described in
[formats/CBMP.md](formats/CBMP.md). Exterior/interior regions were excluded;
transparency, text and broader image variants remain unvalidated. Metadata is
in [bitmap-recovery-evidence.json](bitmap-recovery-evidence.json).

**Observed static postread scope:** NE `0001:8462` searches a tag/pattern registry
and leaves missing tags unchanged. Startup registers17 types, excluding CBMP
and PSND. The full interpreter remains unresolved for registered types; this
does not establish byte preservation for all resources. Detailed addresses and
source hashes are in [ARCHIVE-CONSUMERS.md](ARCHIVE-CONSUMERS.md).

**Observed:** sequential PSND1 conversion and source playback parameters are
now recovered: mono 8-bit 22,050 Hz, second-order byte integration. All 1,278
integer calls and81,792 converted samples/final state match original routines.
[formats/PSND.md](formats/PSND.md) records exact source addresses, getter bindings
and scope. **Unknown:** live resource-to-scene mapping/comparison, sound
seek/loop semantics, other variants, and one recovered gameplay operation.
M1 remains incomplete.

## Difference from earlier ports

The owner’s Stickarcade and Monstersmash projects began with GameMaker project material. Their Karoshi projects recovered GameMaker content through existing tools and used recovered GML in a small interpreter. The inspected Yukon Windows files offer no equivalent recovered source-level starting point. Shared web presentation experience remains useful, but a Yukon importer and behavior model still need to be established.
