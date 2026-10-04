# Instructions for coding agents

## Purpose and starting point

Build a faithful, pleasant web version of The Yukon Trail from the supplied disc. The user’s current request takes precedence over this plan. Read `README.md`, `docs/STATUS.md`, and the relevant milestone in `docs/ROADMAP.md` before working. Read `docs/FINDINGS.md` before interpreting binaries and `docs/WORKFLOW.md` before implementing extraction or recovered behavior.

The repository is at the investigation stage. There is no application or chosen language yet. When asked to continue implementation without a narrower task, take the earliest actionable item in `docs/STATUS.md`. Work toward a concrete, verifiable result; do not replace that work with another general plan. Do not treat a documentation-only request as authorization to implement the game.

## Evidence and fidelity

- Use the original binary, resources, and observed original-game behavior as the reference. External remakes and AI-generated explanations are leads, not proof.
- Distinguish **observed**, **inferred**, and **unknown** claims. Attach the source file/hash and resource ID, file offset, or executable address to reverse-engineering findings. For NE addresses, preserve segment:offset and the analysis tool’s mapping rather than inventing a flat address.
- Resource type names do not establish their semantics. In particular, `SCRP` is not confirmed to be editable source or a general-purpose script VM.
- Check decompiler output against disassembly and callers for uncertain types, signedness, sizes, segmented pointers, and control flow. Persist names and types in the analysis project and export the useful findings into versioned documentation.
- Keep raw evidence separate from interpretations. Record unanswered questions instead of filling gaps with plausible game mechanics.
- Validate recovered behavior against the original. Tests whose expected values come only from the new implementation do not demonstrate fidelity.

## Implementation boundaries

- Preserve the ISO unchanged. Extract into a separate directory and verify source hashes. Never modify original files to simplify parsing.
- Keep original media, extracted assets, saves, emulator disks, and bulky Ghidra projects in the ignored locations documented in `original/README.md`. Commit reproducible tools, format specifications, metadata, and small synthetic test fixtures.
- Do not add a package manifest, framework, dependencies, or CI merely as placeholders. Make the runtime decision after the proof milestone and record its evidence and tradeoffs.
- Separate asset import, recovered game state/rules, platform services, and presentation. Keep time and randomness controllable for comparisons.
- Preserve original resource IDs and provenance through conversions. Fail explicitly on unsupported formats or opcodes; do not silently invent defaults or skip behavior.
- Keep usability changes explicit. Do not alter rules, timing, dialogue, or progression as incidental refactoring.
- Do not choose a license for the owner or treat the availability of an archive as a distribution decision. Publishing original assets is outside routine repository bootstrap.

## Verification and handoff

Run checks appropriate to the work: source identity and archive invariants for importers, independent expected outputs for decoders, original-versus-port state comparisons for rules, and browser checks for presentation. Add meaningful tests for parsers and recovered logic; avoid tests that only repeat implementation details.

At the end of a meaningful work session:

1. Update `docs/STATUS.md` with completed work, actual checks and results, unresolved issues, and the next concrete action.
2. Update the relevant finding or format specification with new evidence. Record architectural decisions with alternatives and reasons in the roadmap or a dedicated decision document when needed.
3. Document commands, versions, and necessary local artifacts so another agent can reproduce the result. Temporary paths alone are not a handoff.
4. Review `git diff` and `git status`; make sure no source media, generated assets, or unrelated changes enter the patch.

Do not claim the project or a milestone is complete based only on compilation, screenshots, or a successful opening sequence. Report validation scope and any untested paths plainly.
