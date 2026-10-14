# The Yukon Trail — web preservation project

This project aims to preserve **The Yukon Trail** as a faithful, enjoyable browser game. The starting point is an Internet Archive disc image supplied by the project owner. The target is a web-hosted experience with the original game’s content and behavior, appropriate browser controls, and reliable saves.

**Status: source recovery and analysis setup.** The Windows extraction is
verified, a tested archive-index reader is available, the Mac catalog/forks have
been inventoried without extraction, and a persistent Ghidra NE project has
been imported and reopened. Windows 3.1 boots in the local DOSBox-X reference
environment; a blind subagent playthrough reached the original game's
return-home newspaper ending and Claims of Fame. A bounded decoder recovers two
original speech bubbles, with native-code and border-pixel comparisons passing.
All 331 CBMP resources (1,523 frames) pass the bounded decoder; selected Seattle
background/sprite integer routines and a bounded Linda contribution/money model
have additional original-code checks. These are recovery results, not a playable
Seattle slice. The authorized AppleScript fallback now supports a fresh constrained Seattle
reference session; an independent worker is recording it. Selected journal and
postread transformations also match bounded original-code execution.
A sequential PSND1/616 decoder matches original integer/sample-conversion
routines. PSND616 maps to Linda's recorded storm speech with a bounded waveform
comparison and documented residuals; PSND1's live case remains unidentified. There is no playable
port. The bounded proof supports JavaScript modules/2D canvas; the first browser
rule module matches original money/eligibility checks. No framework is required.

## Start here

- [Agent instructions](AGENTS.md): how to work and leave a useful handoff.
- [Current status and next work](docs/STATUS.md): the authoritative execution checkpoint.
- [Roadmap](docs/ROADMAP.md): milestones with evidence-based completion criteria.
- [Disc and binary findings](docs/FINDINGS.md): observations, archive layout, and unresolved questions.
- [Working method](docs/WORKFLOW.md): extraction, reverse engineering, validation, and evidence records.
- [Research and reusable tools](docs/RESEARCH.md): relevant AI-assisted ports and established practices.
- [Source manifest](docs/source-manifest.json): file sizes, hashes, and provenance gaps.
- [Source provenance verification](docs/SOURCE-PROVENANCE.md): Archive checksum match and file inventory.
- [Windows extraction metadata](docs/windows-extraction.json): identities of all 16 selected files.
- [Original-game reference setup](docs/REFERENCE.md): Windows, drivers, configuration, and captures.
- [Reference environment manifest](docs/reference-environment.json): exact local identities and validation scope.
- [Blind original-game playthrough](docs/BLIND-PLAYTHROUGH.md): one completed run, choices, ending evidence, and limits.
- [Story reconstruction](docs/STORY-RECONSTRUCTION.md): a readable start-to-end account of the recorded journey with Linda, with evidence and unexplored branches.
- [Mac source inventory](docs/MAC-SOURCE.md): catalog, fork hashes, and extraction limits.
- [Binary analysis setup](docs/ANALYSIS.md): local Ghidra project, segmented mappings, and tool limitations.
- [Archive consumer evidence](docs/ARCHIVE-CONSUMERS.md): original read/lookup routines and persisted annotations.
- [Postread transformations](docs/formats/POSTREAD.md): original startup patterns and bounded native buffer comparisons.
- [Archive-index specification](docs/formats/YUKONRES.md): validated reader and byte-preserving raw exports.
- [Selected image recovery](docs/formats/CBMP.md): frame/packed formats, original palette, and native comparisons.
- [Selected sound recovery](docs/formats/PSND.md): sequential samples, playback parameters, and original-code checks.
- [Runtime decision](docs/RUNTIME-DECISION.md): bounded proof, selected JavaScript/canvas approach and alternatives.
- [Validation coverage](docs/COVERAGE.md): discovered original cases, recovery scope and pending port checks.
- [Seattle operation recovery](docs/SEATTLE-RULES.md): bounded partner contribution and original money arithmetic.
- [Seattle reference handoff](docs/SEATTLE-REFERENCE.md): isolated restored guest and native UI access limitation.
- [Original font evidence](docs/FONT-EVIDENCE.md): supplied TrueType identity and remaining rasterization questions.
- [Image composition](docs/IMAGE-COMPOSITING.md): original copy modes and remaining selected-scene gaps.

## What we have learned

The supplied `original/iso/YUKONCD.ISO` is a 370,939,904-byte hybrid disc image with an ISO9660 file tree and a classic Macintosh HFS partition. Its Windows files are readable with `bsdtar`; the disc does not need generic decompression before inspection.

The principal Windows files are a 404,272-byte Windows 3.x NE executable, `YUKON.EXE`, and an 87,911,322-byte custom MECC resource archive, `YUKONRES`. The executable identifies version 1.1. No original source code was found in the inspected Windows tree. We expect to recover assets, data formats, and behavior through reverse engineering rather than restore the original editable source project.

The archive contains **2,522 records across 21 types**. The reusable reader checks
bounds, keys, groups, and payload overlaps, and exports explicitly requested raw
records with provenance. Image, audio, scene, and script-like resource names are
promising; two selected CBMP images are now decoded, while other payload formats
and execution semantics need further evidence.
The Mac `YUKONRES` data fork has the same size/hash as the Windows archive. Its
filesystem has been inventoried, but its forks have not yet been extracted.

The supplied ISO matches the published checksums for the owner's
[Internet Archive item](https://archive.org/details/YUKONCD). Its current listing
contains no separate audio-track files. The disc README describes bonus tracks
2–18, but their relationship to in-game music remains unverified; see
[the source inventory](docs/SOURCE-PROVENANCE.md) and
[audio evidence](docs/AUDIO-EVIDENCE.md).

## Implementation direction

Preserve the original game’s rules and content first. Keep intentional usability improvements distinguishable from fidelity fixes. The owner has used React Three Fiber successfully on earlier ports but has no required framework for this project.

The bounded recovery proof now includes selected images, source-mapped sound,
and the independent immediate Linda contribution/journal comparison. The runtime
decision is JavaScript modules with a2D canvas, with import, rules, platform
services and presentation separated. [The decision](docs/RUNTIME-DECISION.md)
records TypeScript, C++/WebAssembly and browser-emulation alternatives, reasons
and remaining limits. Browser emulation remains untested as a fallback.
The first rule modules have original-oracle checks; the actual Seattle slice,
save round trip and browser presentation still need implementation/validation.

## Local source material

Place the supplied image at `original/iso/YUKONCD.ISO`. Original files, extracted game assets, emulator images, and local analysis projects are excluded from Git. See [source storage](original/README.md) for the directory convention.

From the repository root, these commands inspect the source without running it:

```sh
shasum -a 256 original/iso/YUKONCD.ISO
bsdtar -tf original/iso/YUKONCD.ISO
```

Expected ISO SHA-256:

```text
89f8eb97bd7d3afdbabbd05dce10854673eff5c5617825940994aba7a0360ed8
```

The importers, image/sound decoders and synthetic tests use Python's standard library;
Python 3.14.5 was used locally. An optional analysis verifier uses a locally
staged Unicorn 2.1.4 to execute isolated original integer readers:

```sh
python3 -m unittest discover -s tests -v
python3 tools/verify_source_files.py
python3 tools/yukonres.py original/extracted/windows/YUKONRES \
  --output-dir generated/yukonres-index --extract CBMP:1 --extract PSND:1
```

Choose a fresh output directory when repeating an export. Tests use small
synthetic fixtures and require no source media. See the workflow and tool-specific
documents for complete extraction, HFS inventory, and analysis commands.
A partial local opening build and exact asset preparation/run commands are in
[PORT-RUN.md](docs/PORT-RUN.md). Browser execution, Seattle interaction, save/load
and the playable milestone remain unverified/incomplete. Run the browser rule
original-oracle check with `node tests/test_browser_seattle.mjs` (Node26.0.0 tested). Do not commit the disc or silently
bundle its assets into a public build. Project-code licensing and the asset
distribution approach are still undecided.
