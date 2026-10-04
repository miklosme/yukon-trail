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

These are directory conventions; most directories do not exist yet. Put small, durable interpretation notes and evidence metadata in `docs/`. Do not rely exclusively on ignored files or temporary paths for findings needed by another agent.

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

The initial investigation used `bsdtar` for these selected files. This is not yet a full installer extraction or a Mac extraction procedure. Avoid overwriting an existing working extraction; use a new location if it contains changed files. Inspect the archive listing before expanding extraction scope.

## Reference runtime

Inventory the emulator and system material already available before installing anything. [DOSBox-X’s Windows 3.1 guide](https://dosbox-x.com/wiki/Guide:Installing-Windows-3.1x) is the initial reference; neither DOSBox-X compatibility with this exact disc nor a working setup has been demonstrated here.

Record emulator version, system version, display driver/resolution/color depth, sound configuration, mounted paths/disc identity, installation choices, and launch steps. Separate full-game and demo observations. Preserve a known baseline save or snapshot and document how to restore it. Capture the original’s behavior before writing the equivalent rule.

## Binary analysis loop

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
