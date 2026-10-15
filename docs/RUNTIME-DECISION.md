# Runtime decision

Decision date: 2026-10-13. Use native JavaScript modules with explicit integer
operations and a 2D canvas renderer for the local port. Keep asset conversion in
Python and game state separate from browser presentation/services. No framework,
package manifest or build dependency is needed for the initial slice. This is an
implementation decision after the bounded proof, not a claim of a playable build.

## Evidence supporting the decision

The archive reader preserves type/ID/offset/hash identity. The postread transformer
matches full original instruction execution on1,274 bounded source records;
selected scene data is structured resource content, with semantics still traced
through callers. Nothing establishes SCRP as editable source or a general VM.
Selected images decode with exact native integer comparisons, bubble borders
match original captures, and the selected Wharf background matches120,000 pixels
with explicitly documented display palette handling. PSND1/616 decode to
source-established mono8-bit22,050Hz samples with exact native integer/sample
agreement; PSND616's original recording comparison retains14.36% fitted residual.
A bounded clock diagnostic across±0.1% finds its best fit at unchanged rate;
this does not explain the residual or justify changing playback speed.

The independently recorded Linda case now supplies the visible operation proof:
immediate Aug24 Seattle journal cash350→850, unchanged0lb/date, and an appended
entry matching the executable/CSTR-derived formatter byte-for-byte after visual
transcription. Capture identities and limits are in
[linda-live-comparison.json](linda-live-comparison.json). Hidden state was not read
from guest memory. Native arithmetic, formatting, queue and eligibility checks
cover their bounded subsets; full scene activation remains separate recovery.

These establish a small M1 recovery proof with documented limits. They do not
establish general rendering, whole-audio fidelity, full dialogue execution or M2.
The proof specifications are formats/YUKONRES.md, formats/POSTREAD.md,
formats/CBMP.md, formats/PSND.md, IMAGE-COMPOSITING.md and SEATTLE-RULES.md.

## Alternatives considered

| Option | Benefit | Cost / uncertainty | Decision |
| --- | --- | --- | --- |
| JavaScript modules / canvas | Direct pixel buffers, browser input/audio/storage; explicit16-bit operations; no compile toolchain for local slice | Original segmented/virtual dispatch must be translated and checked; runtime types require input validation | Choose for initial port |
| TypeScript / canvas | Static checks for resource/state structures | Adds compilation/toolchain before useful volume of runtime code exists; types do not prove fidelity | Adopted 2026-10-14 (see revision below) |
| C++ / WebAssembly | Fits substantial recovered native arithmetic and pointer-oriented code | No original source available; Windows GDI, messages, allocation and segmented pointers need adaptation; same recovery work with added integration | Do not choose for present bounded workload; isolate kernels if later measurements justify |
| Browser DOSBox-X emulation | Could preserve original executable rules and alternate paths | Requires a browser-compatible Windows guest, bounded performance/audio/persistence tests and separately provisioned system media; browser UI must respect original controls | Retain as measurable fallback, not selected without tests |

The [js-dos DOSBox-X backend documentation](https://js-dos.com/dosbox-x.html)
describes worker execution and operating-system support. Its
[bundle specification](https://js-dos.com/jsdos-bundle.html) defines a ZIP/config
container. These are feasibility leads only: this repository has not run the
original through that browser backend. No third-party guest image is adopted.

## Boundaries for implementation

Importers generate ignored local assets with source provenance; unsupported
formats/fields fail explicitly. Runtime state/rules use controllable time and
randomness only where recovered, preserve original widths and distinguish
unsigned words from signed comparisons. The canvas retains the original640×480
composition and scales as a whole; use original backgrounds, controls and menus.
Text/font positioning, sprite draw modes and hit regions need their own observed
comparisons. Do not replace them with a guessed modern interface.

Browser services handle audio activation and save persistence independently.
Use original save/menu affordances where recovered; document and review any
necessary browser accommodation. Native save container/header decisions now have original-instruction checks;
full restoration and browser persistence remain unvalidated. No public deployment, license choice or asset distribution decision
is included. Human review is due when the actual Seattle slice and its verified
exit/save round trip are playable.

Next concrete implementation prerequisite: finish the selected scene/hotspot
consumer trace and the observed Seattle dialogue/purchase/exit sequence, then
build that bounded interaction with explicit unsupported behavior. A rendered
background or single recruitment demo is not the M2 milestone.

Initial runtime rule handoff: `web/rules/seattle.ts` and `journal.ts` now
implement bounded source-established money, Linda eligibility, selected journal
formatting and queue writes. Node26.0.0 checks match original400 money cases,
16 eligibility cases,576 journal cases and3 queue cases. See STATUS.md for
local vocabulary preparation and exact commands. No state defaults, invented
calendar progression, game UI or generic dialogue engine are supplied.


The emulation fallback now has a frozen, verified local input package; see
BROWSER-EMULATION-EVALUATION.md. Recovery has exposed tightly coupled Win16
scene construction, sprite interception, scheduling and platform controls.
Preserving those original paths through a compatible backend is a concrete
potential benefit, but source packaging does not prove compatibility. Measure
the trial's viewport/input/sound, saves, complete/alternate journeys and supported
browsers before choosing it or changing the native JavaScript architecture.

## Revision 2026-10-14: TypeScript source, Vite serving, Bun tooling

At the owner's direction the port moved from untyped `.mjs` modules served by a
Python loopback server to TypeScript (`web/**/*.ts`) served and bundled by Vite,
with Bun running the oracle scripts. The 2026-10-13 architecture is unchanged:
2D canvas presentation, Python asset conversion, and import/rules/platform/
presentation separation. Only the language and the serving toolchain changed.

Reasons: the repository had already been initialised with Bun and a strict
`tsconfig.json`, so continuing in plain JavaScript left the port without types
or a dependency manifest; the rule modules now carry explicit interfaces for the
recovered JSON vocabularies, state words and byte buffers that `main.ts`
consumes; and Vite provides the module dev server and build that the Python
static server could not for TypeScript. Costs accepted: a `node_modules`
toolchain (vite, typescript, @types/bun), and `noUncheckedIndexedAccess` is off
because the byte-level rules index typed arrays after explicit length checks.

Fidelity evidence: every runtime guard and throw was preserved during the
conversion, and the original-instruction oracle checks were rerun unchanged
except for import paths: 19 self-contained checks pass under both Bun 1.3.14
and Node 26.0.0, and the eight checks that take local prepared inputs (TREE
graphs, opening journal, Linda journal, voices, cached frames, population,
purchase, saves) plus the pinned-emulator contract check pass. Types do not add
fidelity evidence; no browser execution was verified in this revision.

## Revision 2026-10-14: automatic formatting for the web port

At the owner's direction the repository adopts Prettier for `web/**/*.{ts,html,css}`,
mirroring the owner's setup in another project: Prettier options live in
`package.json` (print width 100, single quotes, trailing commas, no semicolons,
`prettier-plugin-organize-imports` with destructive code actions disabled), `bun run
format` rewrites the web port, `bun run format:check` verifies it, and
`simple-git-hooks` installs a pre-commit hook that runs `pretty-quick --staged`.
`.prettierignore` excludes everything outside `web/`, so the oracle scripts in
`tests/`, the Python tooling, documentation and fixtures are never rewritten.

Dev dependencies added: prettier, prettier-plugin-organize-imports, pretty-quick,
simple-git-hooks. Reason: consistent layout for the growing typed port without a
hand-maintained style guide. Cost accepted: four tooling packages and a `prepare`
script that installs the hook on `bun install` (`SKIP_SIMPLE_GIT_HOOKS=1` bypasses
it). Formatting is layout only; it does not change rules, timing or behaviour, and
the typecheck and oracle checks were rerun after the initial reformat.
