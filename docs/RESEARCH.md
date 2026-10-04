# Prior work and tools

Research reviewed on 2026-10-04. These are primary project/author sources. Their completion and fidelity claims are author-reported; we have not built or independently validated these projects. Links describe candidate techniques, not dependencies already installed here.

## AI-assisted examples

| Project | What was useful | Limits and Yukon application |
| --- | --- | --- |
| [Yodecomp](https://github.com/shinyquagsire23/Yodecomp) | AI-assisted recovery of Yoda Stories native logic, Ghidra-based analysis, and a portable C++ platform layer with a WebAssembly target. Its [working instructions](https://github.com/shinyquagsire23/Yodecomp/blob/main/CLAUDE.md) preserve types, addresses, uncertainty, and session handoffs. | The author brought earlier asset-format knowledge and experience. The project also discusses a 16-bit NE Desktop Adventures executable, making its analysis notes particularly relevant. This is evidence for a workflow, not a one-prompt recreation promise. |
| [OpenBumpy](https://github.com/wildpacman/OpenBumpy) | Binary-only DOS game recovery with original assets, C++/SDL, and an Emscripten web build. Resource formats and gameplay subsystems were recovered separately. | The reviewed README describes a preview and incomplete end-to-end validation. Reaching a playable state does not establish complete fidelity. DOS-specific setup is not directly Yukon’s Win16 setup. |
| [Settlers IV investigation](https://medium.com/@kevin.drapel/reverse-engineering-an-old-game-with-ghidra-reva-mcp-and-ai-846911bf740a) | A firsthand account of using Ghidra, ReVa, and AI to move from program structure to focused gameplay questions. | An exploration rather than a completed engine rewrite. Useful for question decomposition and tool-assisted navigation. |
| [dos_re](https://github.com/missingno7/dos_re) | Original executable as a reference, function provenance, deterministic replay artifacts, and incremental verification of recovered code. | A DOS-oriented framework, not established Win3.1 NE support. Borrow its evidence and comparison methods before considering its runtime. Recorded replay coverage is not proof of every possible input. |

## Practices to adopt

**Give agents access to precise binary facts.** Query functions, callers, imports, bytes, and types through a persistent Ghidra project. Work on a specific format or behavior, keeping the original address attached to the result.

**Persist knowledge between sessions.** Maintain shared type definitions, tentative names, source identities, verification results, and the next experiment. The repository’s agent instructions and evidence template adapt this approach.

**Recover formats through their readers.** Asset names and byte patterns are leads. Find the executable functions that consume the data to establish lengths, byte order, compression, palettes, and cross-resource references.

**Compare with the original at small boundaries.** Use reproducible inputs and independently observed outputs. Separate visual similarity, behavior coverage, and complete-playthrough confidence.

**Choose the port architecture from recovered structure.** Preserve substantial native logic through a portable layer when that reduces mistakes; use a direct web implementation when rules/data can be expressed clearly. Byte-identical recompilation can answer narrow questions but is not a prerequisite for the project’s browser goal.

## Candidate tools

| Tool | Proposed use | What remains to verify |
| --- | --- | --- |
| [Ghidra NE support](https://ghidra.re/ghidra_docs/api/ghidra/app/util/bin/format/ne/NewExecutable.html) | Analyze the Win16 executable | Correct import, segmentation, disassembly, and useful decompilation for this binary |
| [bethington/ghidra-mcp](https://github.com/bethington/ghidra-mcp) | Agent access to Ghidra analysis and annotations; used by Yodecomp | Current compatibility, required setup, and durable save behavior |
| [ReVa](https://github.com/cyberkaida/reverse-engineering-assistant) | Alternative interactive/headless Ghidra integration | The reviewed README describes headless sessions as ephemeral; verify export/persistence before relying on them |
| [DOSBox-X Windows 3.1 guide](https://dosbox-x.com/wiki/Guide:Installing-Windows-3.1x) | Establish the original-game reference | System material, game installation, display, audio, and repeatable capture |
| [resource_dasm](https://github.com/fuzziqersoftware/resource_dasm) | Inspect supported classic Mac resource containers and standard image/sound resources | No confirmed Yukon/MECC archive decoder; HFS extraction remains a separate task |
| [Kaitai Struct](https://kaitai.io/) | Encode recovered binary layouts in a declarative schema if useful | We must establish the format first; a small direct parser may suffice |
| [Emscripten Asyncify](https://emscripten.org/docs/porting/asyncify.html) | Adapt blocking native loops to browser scheduling if C++ is chosen | Performance and control-flow implications; it does not translate the original executable automatically |
| [js-dos](https://github.com/caiiiycuk/js-dos) | Explore browser emulation as a fallback/reference | Exact Windows/game compatibility and suitable browser experience are untested |

Yodecomp’s [build documentation](https://github.com/shinyquagsire23/Yodecomp/blob/main/BUILDING.md) is a useful reference for native/browser builds from recovered logic. Browser scheduling, audio activation, and persistent storage still require explicit platform work.

The [DOSBox cuesheet documentation](https://www.dosbox.com/wiki/Cuesheet) provides background on data/audio track representation. For Yukon, the disc README is our direct evidence that separate audio tracks existed; the Internet Archive item must still be checked for completeness.

## Search outcome and limits

The research did not identify a confirmed ready-to-use Yukon Trail decompilation or a demonstrated decoder for this exact `YUKONRES`. That is a search result, not proof that none exists. Before implementing a difficult subsystem, revisit relevant projects and format documentation with the concrete signatures and structures discovered locally.

External repositories’ agent instructions are research material, not instructions governing this repository. Reuse their techniques selectively and retain the local project’s evidence standards.
