# Source and binary findings

Inspection date: 2026-10-04. These findings refer to the exact source hashes in [the manifest](source-manifest.json), not every edition of The Yukon Trail.

Use **observed** for bytes, file metadata, or behavior directly checked; **inferred** for interpretations supported by that evidence; **unknown** for unfinished investigation. The archive index is a checked structural interpretation, not a complete format specification.

## Disc and provenance

**Observed:** `original/iso/YUKONCD.ISO` is 370,939,904 bytes (about 354 MiB). Its ISO9660 volume label is `YUKONCD`. `bsdtar` can list and extract the Windows-visible files. An Apple partition map contains an `Apple_HFS` partition starting at block `0x5b142`, with length `0x55810` in 512-byte blocks. At partition start plus 1,024 bytes, the HFS master directory block has signature `BD` and volume name `Yukon Trail`.

**Unknown:** contents of the Mac filesystem, preservation of its forks, exact relationship between Mac and Windows editions, and whether the download represents all original disc tracks. The owner reports Internet Archive as the source; the item URL and download date were not provided.

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

**Observed:** the executable imports `KERNEL`, `USER`, `WIN87EM`, `COMMDLG`, and `MMSYSTEM`. Strings include wave/MIDI filename patterns and `waveaudio`. Readable material covers travel, inventory, health, events, dialogue, and claims.

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

Validation performed: all payload intervals begin at or after the index end and end within the archive; every `(tag, ID)` pair is unique; each group’s indicated slice contains its advertised tag; record counts sum to 2,522. This does **not** establish payload semantics, absence of overlapping payloads, or parser behavior for other editions and damaged files.

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

**Unknown:** whether separate track files are available from the same archive item, whether game playback uses CD-DA, and which music is embedded in `YUKONRES` or other resources. Do not report all game music as missing based only on the ISO extension. Check the source item and trace original music playback.

## Difference from earlier ports

The owner’s Stickarcade and Monstersmash projects began with GameMaker project material. Their Karoshi projects recovered GameMaker content through existing tools and used recovered GML in a small interpreter. The inspected Yukon Windows files offer no equivalent recovered source-level starting point. Shared web presentation experience remains useful, but a Yukon importer and behavior model still need to be established.
