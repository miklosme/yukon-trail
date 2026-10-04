# Execution checkpoint

Updated: 2026-10-04. Current phase: source investigation and project bootstrap.

## Completed

- Inspected the ISO9660 tree and selected Windows files without executing the original game.
- Recorded the ISO, executable, and resource archive sizes and SHA-256 hashes in `source-manifest.json`.
- Identified Windows NE format, version 1.1 strings, and the custom MECC archive.
- Identified an Apple partition map and HFS signature; Mac contents remain unextracted.
- Interpreted the archive index and checked all 2,522 entries for payload bounds, unique `(type, ID)` keys, and agreement with the 21 type groups.
- Reviewed primary examples of AI-assisted game reverse engineering and documented applicable practices.
- Added documentation, agent guidance, and Git exclusions for local source material and generated work.

## Not yet done

No original-game execution, persistent Ghidra setup, decoder implementation, gameplay recovery, framework selection, browser port, or playthrough validation. The earlier selected-file extraction was temporary; it is not an installed project dependency or a durable handoff artifact.

## Next work, in order

1. **Reproduce local source extraction.** Verify the ISO hash and extract selected Windows files under `original/extracted/windows/` using the workflow. Verify executable/archive hashes. Record a listing and source provenance. Investigate safe HFS extraction that preserves resource forks; keep its output separate.
2. **Establish the original-game reference.** Inventory available emulator and Windows 3.1 installation material, configure a reference runtime, and reach the opening playable scene. Record the environment, display/audio settings, installation procedure, and a replayable observation. Do not assume that DOSBox alone runs a Windows NE program. If required system media is unavailable, record that dependency and continue static analysis.
3. **Create durable binary analysis.** Evaluate Ghidra NE import and one Ghidra integration from the research notes. Verify that the project survives a restart. Trace archive opening/lookup and image/audio consumers; record function addresses and tentative structures.
4. **Implement the bounded proof.** Build a validated archive reader, recover one image and one sound from `YUKONRES`, and trace one operation such as a shop purchase. Compare rendering/audio/state with the original before deciding the application runtime.

See [milestones and exit criteria](ROADMAP.md) for what constitutes completion. These items are the next implementation work, not claims that tooling has already been installed.

## Open inputs and decisions

| Item | Current state | Work that can proceed |
| --- | --- | --- |
| Internet Archive item URL and download metadata | Not supplied | Local extraction and binary analysis |
| Separate CD audio tracks | Disc README lists tracks 2–18; availability and in-game dependency unknown | Resource audio investigation |
| Reference system media and emulator setup | Not inventoried/configured | Static analysis and importer work |
| Mac executable/resources | Partition detected; not extracted | Windows work |
| TypeScript versus C++/WebAssembly | Deferred until proof milestone | Extraction and behavior research |
| Project license and asset distribution | Undecided | Local tooling and documentation |

## Verification at bootstrap

Source hashes were recalculated from the local files. A read-only exploratory inspection confirmed the archive invariants documented in `FINDINGS.md`; no reusable extractor or parser tests exist yet. Documentation links and manifest structure were checked locally. No gameplay fidelity claim has been made.
