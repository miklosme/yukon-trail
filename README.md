# The Yukon Trail — web preservation project

This project aims to preserve **The Yukon Trail** as a faithful, enjoyable browser game. The starting point is an Internet Archive disc image supplied by the project owner. The target is a web-hosted experience with the original game’s content and behavior, appropriate browser controls, and reliable saves.

**Status: investigation and repository bootstrap.** There is no playable port, asset decoder, Ghidra project, or configured original-game runtime yet. No application framework has been selected.

## Start here

- [Agent instructions](AGENTS.md): how to work and leave a useful handoff.
- [Current status and next work](docs/STATUS.md): the authoritative execution checkpoint.
- [Roadmap](docs/ROADMAP.md): milestones with evidence-based completion criteria.
- [Disc and binary findings](docs/FINDINGS.md): observations, archive layout, and unresolved questions.
- [Working method](docs/WORKFLOW.md): extraction, reverse engineering, validation, and evidence records.
- [Research and reusable tools](docs/RESEARCH.md): relevant AI-assisted ports and established practices.
- [Source manifest](docs/source-manifest.json): file sizes, hashes, and provenance gaps.

## What we have learned

The supplied `original/iso/YUKONCD.ISO` is a 370,939,904-byte hybrid disc image with an ISO9660 file tree and a classic Macintosh HFS partition. Its Windows files are readable with `bsdtar`; the disc does not need generic decompression before inspection.

The principal Windows files are a 404,272-byte Windows 3.x NE executable, `YUKON.EXE`, and an 87,911,322-byte custom MECC resource archive, `YUKONRES`. The executable identifies version 1.1. No original source code was found in the inspected Windows tree. We expect to recover assets, data formats, and behavior through reverse engineering rather than restore the original editable source project.

The archive has a strongly supported index interpretation containing **2,522 records across 21 types**. Bounds, key uniqueness, and group membership have been checked. Image, audio, scene, and script-like resource names are promising, but their payload formats and execution semantics remain unproven. The Macintosh contents have not yet been extracted.

The disc README also describes separate audio tracks 2–18. We have not established whether the download includes those tracks, or whether they are needed for in-game music. The Internet Archive item URL is still missing from our provenance record.

## Implementation direction

Preserve the original game’s rules and content first. Keep intentional usability improvements distinguishable from fidelity fixes. The owner has used React Three Fiber successfully on earlier ports but has no required framework for this project.

The first implementation milestone will recover one image, one sound, and one observable gameplay operation, checked against the running original. Then choose the runtime:

- **TypeScript with a 2D renderer and optional React shell** if the resource data and recovered rules are straightforward to express directly.
- **C++ compiled to WebAssembly**, with a browser shell as needed, if preserving substantial recovered native logic reduces translation risk.

Browser emulation remains a possible reference or fallback. Compatibility and user experience have not been tested. Do not scaffold a renderer before resolving the first milestone’s architectural questions.

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

There are no install, build, or test commands yet. Add reproducible commands when their corresponding tools are implemented. Do not commit the disc or silently bundle its assets into a public build. Project-code licensing and the asset distribution approach are still undecided.
