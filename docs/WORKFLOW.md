# Working method

## Local layout

Keep documentation and future tools in Git. Use these ignored locations for local working data:

```text
original/iso/                  supplied disc image and accompanying tracks
original/extracted/windows/   files extracted from the ISO9660 tree
original/extracted/mac/       Mac extraction with forks preserved
local/ghidra/                 persistent analysis project and backups
local/emulator/               emulator configuration, system disks, runtime saves
local/evidence/               original-game captures and replay evidence
generated/                    converted resources and generated manifests
public/game-assets/           optional future staged deployment assets
```

These are directory conventions. Put small, durable interpretation notes and evidence metadata in `docs/`. Do not rely exclusively on ignored files or temporary paths for findings needed by another agent.

## Reproduce the Windows extraction

Run from the repository root. Check the hash against `docs/source-manifest.json` before interpreting the files as this edition:

```sh
shasum -a 256 original/iso/YUKONCD.ISO
bsdtar -tf original/iso/YUKONCD.ISO
```

For a fresh extraction directory, a selected-file extraction can begin with:

```sh
mkdir -p original/extracted/windows
bsdtar -xf original/iso/YUKONCD.ISO -C original/extracted/windows \
  YUKON.EXE YUKONRES YUKONCD.INF YUKHELP.HLP YUF_____.TTF \
  YLOGO.BMP README.TXT READINGS LICENSE.TXT
shasum -a 256 original/extracted/windows/YUKON.EXE \
  original/extracted/windows/YUKONRES
```

The durable selected extraction was reproduced on 2026-10-04 with `bsdtar`
3.5.3 / libarchive 3.5.3. [Its metadata manifest](windows-extraction.json)
records all 16 extracted files, their sizes/hashes, and the 489-line ISO listing
identity. Preserve the listing locally:

```sh
mkdir -p local/evidence
LC_ALL=C bsdtar -tf original/iso/YUKONCD.ISO > local/evidence/iso9660-listing.txt
python3 tools/verify_source_files.py > local/evidence/windows-direct-verification.json
```

The verifier first checks the ISO size/SHA-256 and extraction provenance. It
then compares each of the 16 selected extracted files with its versioned
identity and a fresh `bsdtar -xOf` stream directly from the disc. This is
independent of the resource reader and extracted copies; it uses the same
libarchive container parser as extraction, so it is not independent validation
of ISO parsing. It is read-only and emits JSON only after
every check succeeds; check its exit status before using a redirected report.
`bsdtar` must be available on `PATH`; version 3.5.3 was used here.
Ten synthetic tests use a tiny independently written tar container, not game
bytes or a claim about ISO parsing. They exercise source/extraction drift,
inconsistent metadata, missing entries, and ambiguous/duplicate/pattern paths.
Selected paths containing glob/escape characters fail explicitly because
`bsdtar` otherwise interprets them as patterns rather than exact entry names.

The owner-supplied Archive item and published checksum/file inventory are
verified in [SOURCE-PROVENANCE.md](SOURCE-PROVENANCE.md). The local ISO matches
its published size, MD5, SHA-1 and CRC32; the local SHA-256 remains the stronger
recorded identity. No ISO was downloaded again.

This is not a full installer extraction or a Mac extraction procedure. Avoid
overwriting an existing working extraction; use a new location if it contains
changed files. Inspect the archive listing before expanding extraction scope.
The reference setup mounts the full ISO for the installer; see
[actual inventory and proposed setup](REFERENCE.md). Mac inventory and the
fork-preserving extraction recommendation are in [MAC-SOURCE.md](MAC-SOURCE.md).

## Reference runtime

Inventory the emulator and system material already available before installing anything. [DOSBox-X’s Windows 3.1 guide](https://dosbox-x.com/wiki/Guide:Installing-Windows-3.1x) is the initial setup reference; this project's demonstrated environment is recorded below.

Record emulator version, system version, display driver/resolution/color depth, sound configuration, mounted paths/disc identity, installation choices, and launch steps. Separate full-game and demo observations. Preserve a known baseline save or snapshot and document how to restore it. Capture the original's behavior before writing the equivalent rule.

DOSBox-X has now been staged in ignored `local/tools/dosbox-x/` and launched.
Separately provisioned Windows 3.1 OEM boots in 386 Enhanced Mode with S3/SB16
drivers; Windows waveform output has a nonzero native PCM capture. Its media,
drivers, reconstructed configuration, backups and actual checks are recorded
in [REFERENCE.md](REFERENCE.md). The original game's opening journal rendered
and native video/audio capture passed integrity checks. Win31 mouse integration
allows reliable pointer control, and a fresh process repeated the opening and
journal dismissal to Seattle Wharf. A later
[blind original-game run](BLIND-PLAYTHROUGH.md) reached a return-home ending and
Claims of Fame. Other paths and original-versus-port comparison remain unverified.

## Binary analysis loop

Selected image decoding and its original-code/native-pixel comparisons reproduce
through [formats/CBMP.md](formats/CBMP.md). The decoder and synthetic tests use
the standard library; the optional original-code verifier uses locally staged
Unicorn 2.1.4. Keep this analysis dependency and generated PNGs out of Git.
Read [AUDIO-EVIDENCE.md](AUDIO-EVIDENCE.md) for the current sound recovery leads.
Sequential sound decoding, original-code comparison and its live mapping gap
are documented in [formats/PSND.md](formats/PSND.md). Optional waveform searches
use existing bundled NumPy and FFmpeg; they do not automatically establish
resource identity. Image and sound CLI exports preserve source provenance and
reject unsupported formats rather than substituting guessed data.

1. Verify input identity and import `YUKON.EXE` into Ghidra using its NE support. Check segmentation, imports, entry points, and address mapping before trusting pseudocode.
2. Configure a Ghidra integration only after inspecting its setup and persistence behavior. Confirm that saved names/types survive reopening. Evaluate the options in `RESEARCH.md`; they are not installed dependencies.
3. Ask narrow questions: which function opens `YUKONRES`, how lookup uses type/ID, which caller consumes a chosen record, or how one purchase updates state.
4. Follow callers, callees, raw data, and disassembly. Track offsets, integer width/signedness, pointer representation, and allocation sizes. In 16-bit binaries, missing cross-references or decompiler output can reflect analysis gaps.
5. Define shared types and descriptive names once. Mark tentative interpretations clearly. For multiple binaries, explicitly identify the active program in every recorded result.
6. Implement the smallest supported decoder/rule, compare it with independent evidence, and persist what changed.

Decompiler output is a working hypothesis. Do not convert an entire pseudocode dump into application code and treat compilation as validation. A small repeated workflow with saved evidence is easier to audit and continue.

## Import and conversion contract

The first importer should accept an explicit input path and output directory, verify the expected archive structure, and emit deterministic metadata keyed by `(type, ID)`. Preserve source hash, original offset/length, conversion parameters, and output hash. Keep undecoded payloads available locally. Diagnostics should identify the unsupported resource precisely.

Validate every read and payload range. Test truncation, invalid counts/offsets, duplicate keys, and malformed payloads with small synthetic fixtures. Check valid real inputs locally without requiring the original archive in public CI. Do not assume index byte order determines payload byte order.

Develop a human-readable format specification before introducing a schema generator. [Kaitai Struct](https://kaitai.io/) can express a recovered format; it does not discover its semantics. Record palette selection, transparency, orientation, sample format/rate, and similar parameters from evidence rather than visual/audio guesswork.

### Implemented archive inventory

The [YUKONRES index specification](formats/YUKONRES.md) and
`tools/yukonres.py` implement source-verified inventory and explicit raw exports.
No payloads are decoded. Python 3.14.5 was used locally; the tool uses only the
standard library and no application runtime has been selected.

```sh
python3 tools/yukonres.py original/extracted/windows/YUKONRES \
  --output-dir generated/yukonres-index \
  --extract CBMP:1 --extract PSND:1 --extract CSTR:500 \
  --extract SCRP:1000 --extract TREE:39
python3 -m unittest discover -s tests -v
```

Use a fresh output directory for another invocation; the tool refuses existing
content. It verifies the archive against `docs/source-manifest.json` before
creating output. Synthetic tests require no source media. Keep exported payloads
and generated manifests ignored; only specifications, tools, tests, and small
source metadata belong in Git.

## Evidence record template

Use a record like this in the relevant format or subsystem document:

```text
Finding ID / short title:
Status: observed | inferred | unknown
Source: filename, SHA-256, edition
Location: resource type:ID and byte offset, or NE segment:offset + tool mapping
Question:
Observation: raw structure or original-game behavior
Interpretation: what the evidence supports
Reproduction: commands, input state, actions, tool versions
Verification: independent expected result, actual result, limitations
Local artifacts: capture/save/project paths and hashes where applicable
Remaining questions / next experiment:
```

Keep copied source text to what is necessary to explain a finding; prefer resource references and summaries. A plausible interpretation with no verification stays inferred.

## Behavioral comparison template

Each replay case should state:

- Original environment and source version; baseline save/snapshot identity.
- Starting scene and relevant money, inventory, health, date, or flags.
- Exact inputs and timing assumptions; controlled random seed/time if actually understood.
- Observed original state changes and visible/audio effects.
- Port state changes, differences, and verdict for this case only.

Start with deterministic actions. If randomness cannot yet be controlled, compare established invariants and record why exact replay is unavailable. A purchase comparison should cover deductions, quantity/weight effects, eligibility, and resulting dialogue as applicable; a screenshot alone cannot prove those rules.

Maintain visual comparisons for palettes, layout, sprites, and hit regions, and state comparisons for game logic. Browser input, audio activation, background-tab timing, and persistence require additional checks even when the recovered logic matches.

## Session handoff

Update `STATUS.md` rather than creating competing task lists. State what was changed, what was checked, what failed or remains uncertain, and the next concrete action. Export essential analysis knowledge to versioned text; the Ghidra database should not be the only record. Add actual build/test/tool commands when they exist, with versions or lockfiles where useful.
