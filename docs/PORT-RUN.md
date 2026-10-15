# Local opening build and reproduction

Updated 2026-10-14. This is an implemented opening build, not the M2 playable
Seattle milestone. Browser execution and presentation remain unverified.
The separate TypeScript modules have original-instruction comparisons run under
Bun/Node; those results do not validate DOM, font loading, audio, browser events
or saves.

## Toolchain

The port source under `web/` is TypeScript served and bundled by Vite; the
oracle scripts under `tests/` are TypeScript run directly by Bun (Node ≥23 type
stripping also works). Asset conversion stays in Python. Versions used on
2026-10-14: Bun 1.3.14, TypeScript 7.0.2, Vite 8.3.4, Node 26.0.0, Python 3.14.5.

```sh
bun install            # dev dependencies only: vite, typescript, @types/bun
bun run typecheck      # tsc over web/, tools/*.ts, vite.config.ts and tests/
bun run test           # every oracle check that needs only docs/ evidence
bun run build          # dist/ (ignored); assets are never bundled
```

`tsconfig.json` is strict with `erasableSyntaxOnly` so the same files run
unbundled under Bun/Node; `tests/tsconfig.json` relaxes strictness because the
scripts read untyped evidence JSON and deliberately pass malformed inputs.
The former `tools/serve_port.py` and its Python test were removed; the Vite
dev/preview server plus `tools/selected-assets.ts` replace them (below).

## Prepare and serve

From the repository root, with the verified Windows extraction installed as
recorded in SOURCE-PROVENANCE.md and original/README.md, choose a fresh ignored
asset directory, then select it for the dev server through `YUKON_ASSETS`
(environment variable or an ignored `.env`; see `.env.example`).

```sh
python3 tools/prepare_seattle_opening.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  original/extracted/windows/YUF_____.TTF public/game-assets/local-opening \
  --journal-status --seattle-population
YUKON_ASSETS=public/game-assets/local-opening bun run dev
```

Open `http://127.0.0.1:8000/` when browser access is authorized. The Vite dev
server binds loopback on the same origin as before, serves only `web/`
(`server.fs.allow`; `/@fs/` requests outside it return 403, unknown paths 404
rather than an index fallback) plus the explicitly selected asset directory on
`/game-assets/`. The mount in `tools/selected-assets.ts` fails closed on dot
segments, empty segments, backslashes, absolute paths, bad percent-encoding and
symlinks leaving the real directory, and it refuses to start without a selected
directory containing `manifest.json`. It does not expose the original-media or
guest directories. `bun run preview` serves the built `dist/` with the same
mounts. Source identities,
resource offsets, packed hashes, converted-index hashes and font identity are
retained in the generated manifest. The explicit black palette entry zero is
inferred from source/capture comparison; it is not a measured GDI return.

The current live server was started with the separately prepared
`public/game-assets/seattle-initial-actors-20261014` directory, containing25CBMP/
152frames, seven interview/refusal TREE graphs,47 native-checked voices, opening
and recovered status/inventory vocabulary, initial population metadata, and the unchanged font.
Its manifest SHA256 is
`e48de28905450694b9a99576b903eef0aab93d0e0d6bf507602861b38964ca36`;
journal-status.json SHA256 is
`1ebcc992142eea5cdc912d579d3e39c01bf483d2e3fb1cf49c6e79c096e1b7da`.
The v2 opening is historical and lacks the status vocabulary now required by
main.ts. Reproduce the current package in a fresh directory with:

```sh
python3 tools/prepare_seattle_opening.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  original/extracted/windows/YUF_____.TTF public/game-assets/FRESH-ACTOR-OPENING \
  --journal-status --seattle-population
YUKON_ASSETS=public/game-assets/FRESH-ACTOR-OPENING bun run dev
bun tests/test_opening_journal_projection.ts public/game-assets/FRESH-ACTOR-OPENING
bun tests/test_browser_journal_status.ts
```

The older `seattle-opening-20261013` package has superseded fragment offsets;
do not use it. A separate `seattle-opening-audio-20261013` package additionally
contains verified PSND3400/3401/3405 conversions, but the opening application
has no audio playback hook yet. Adding WAV files does not establish playback.

## Implemented and unsupported behavior

The build includes the original name prompt, source-derived opening journal,
editable notes, original journal background and three fresh inventory overlays,
Done returning to the Wharf with the recovered initial actor poses, and Game → See Journal & Outfit /Ctrl+J.
Visible opening values are observed August23,1897/$350/0lb. Names currently
require nonempty ASCII; journal text must fit the supported Win16 byte range
and 0x27ff edit limit. Unsupported text fails rather than silently converting.
Hidden original initialization is separately recovered and tested, but is not
connected to a full browser game state yet.

Inventory selection now uses the complete original16-row table. Journal reopening
uses the original current-status dirty/cache gate and preserves edited bytes.
Inputs are an explicitly bounded projection of deterministic reset/activated
Seattle words; holes are not initialized original memory. The0x314-byte projection
is shorter than a full world/save, and never serialized as one. Unknown allocator
contents and RNG seed are not replaced by zero-filled world defaults. The exact
known post-first-summary cache comes from original event0→event4 execution.
The settings value uses the independently observed094 pounds branch; general
Management settings are still unsupported. The original Edit constructor space
insertion now matches the independently compared JPRE/JPOST saves; the caret is
set at the end of the DOM value. Browser Edit behavior remains unverified.

Initial Wharf actors are drawn in source head-to-next order from recovered
population metadata. Explicit controlled clock inputs are zero, partnerffff,
property3200 and first-visit/arrival inputs zero; these are bounded opening
inputs, not a complete world or original wall-clock measurement. All imported
actor frame geometry/hashes match the source decoder. Animation, input pixel
buffers and timer scheduling are not connected. Population metadata SHA256 is
`02d9831fa118bd56b0c908957706363f473dd72b1e4d3cce26079cfeda9863fe`.

Scene navigation, sprite interaction, conversations, purchases, ticket/exit,
save/load, travel, minigames and ending are not connected. Clicking the Wharf
reports unsupported interaction through an exception. File/Edit/Management/Help
behavior is unsupported. Other Game menu entries are visibly disabled in this
partial build: this is an unresolved presentation difference, not a faithful
final control state. Window chrome and CSS are provisional. Source font selection
is known; browser DPI, font rasterization, metrics, scrollbars and layout remain
unverified. No new gameplay controls, debug panel or substitute dialogue were added.

## Original-oracle checks

The standalone journal check uses its own source-vocabulary/provenance schema,
prepared below in a fresh ignored directory; do not substitute the opening
asset package journal.json for that test. The following require the freshly
prepared assets and the versioned original
instruction-execution evidence. Run from the repository root:

```sh
python3 -m unittest discover -s tests
bun tests/test_browser_seattle.ts
bun tests/test_browser_indexed.ts
bun tests/test_browser_initial.ts
bun tests/test_browser_calendar.ts
bun tests/test_browser_purchase.ts
bun tests/test_browser_scene_resources.ts
bun tests/test_browser_tree.ts public/game-assets/local-opening
bun tests/test_browser_opening.ts public/game-assets/local-opening/journal.json
python3 tools/prepare_journal_assets.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  generated/local-opening-check/journal.json
bun tests/test_browser_journal.ts generated/local-opening-check/journal.json
```

`bun run test` runs the checks that need only versioned evidence; the commands
above that take a path need the named ignored inputs. The latest full Python
run passed183 tests. Nine Node commands pass with the current v2 assets:400 money/16 eligibility,
243 copy,36 full reset/RNG,2190 calendar/192 scene-entry,112 purchase,
645 hotspot/5 geometry/36 suspension,176 TREE link/18 dialogue-opening,
576 journal/48 actual Seattle location/3 queue cases, plus manually observed
opening-text and platform-text checks. Tests compare retained original outputs
or independently recorded visible text, rather than expected values generated
by the new rules. The selected rules and source-resource models remain bounded;
none constitutes an original-versus-port browser playthrough.

A tenth Node command checks the new original save container against the actual
native read/write hashes for five preserved evidence saves:

```sh
bun tests/test_browser_save.ts
```

This requires those ignored original save files at the paths in
save-container-recovery-evidence.json. It validates byte preservation and fixed
blocks, not the browser File menu, scene restoration or a save round trip while
playing. See formats/GAM.md for source addresses and original API substitutions.

## Browser access and next review

2026-10-14 update: the browser tool loaded the Vite origin for the first time.
Name → journal → Done → Wharf completed with no console errors after fixing a
pre-existing off-by-one in the actor geometry check (`main.ts` compared an
inclusive extent against the exclusive source rectangle; see STATUS.md). That
is a smoke check of load, module graph, font registration and the opening
flow, not an original-versus-port presentation comparison; the rest of this
section's unverified items stand.

CUA browser access to the exact local URL was rejected by automatic approval
review as user permission denied. The user subsequently authorized local preview and
tests; the exact retry was still rejected because a saved browser preference
blocks the URL. The user then reported clearing the setting; the exact retry still returned
the same saved-preference block. Tool access remains unresolved despite valid
authorization. The authorized AppleScript/System Events fallback applies to original
DOSBox playtesting, not browser automation. Do not substitute headless browsers,
raw browser commands or another browser surface to bypass the denial.

Once authorized, verify first load, source/font hashes, native-size rendering,
name/journal/Done/reopen behavior and console errors before assigning independent
blind and constrained port playtests. M2 review is due after the actual Seattle
loop, verified exit and save round trip work; this opening build is not that
milestone. Desktop Chromium, Safari and Firefox remain provisional targets with
no tested browser versions/results. Public deployment is separate.


## Verified selected Seattle voice package

The current complete selected voice importer checks every requested PCM hash
against the independent original converter evidence before creating output.
Choose a fresh ignored directory:

```sh
python3 tools/prepare_seattle_opening.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  original/extracted/windows/YUF_____.TTF public/game-assets/local-seattle-voices
bun tests/test_browser_voice.ts public/game-assets/local-seattle-voices
```

This prepares11 CBMP/34frames, seven TREE graphs and47 PSND conversions from
seattle-sound-set-recovery-evidence.json. The current verified package is
`public/game-assets/seattle-voices-verified-20261014`; its exact manifest identity
and checks are in browser-voice-adapter-evidence.json. Native PCM validation
covers7,626,207 bytes. A bad native PSND1 oracle was deliberately supplied and
failed before an output directory existed. The default evidence path resolves
against the repository, not an unspecified working directory.

The underlying importer also accepts optional `--sound-evidence PATH` alongside
explicit IDs. Extra manifest fields retain mono/sample-bit/rate, raw source and
native PCM hashes, integration order and declared/consumed/terminal bit counts.
`assets.voice(id)` verifies the generated WAV and PCM identity on load, preserving
cached bytes independently of returned callers. `makeVoiceBuffer(context,voice)`
requires an explicit context and retains the source22050Hz sample rate while
converting unsigned8-bit values to Web Audio floats. No gain, overlap, autoplay,
clock or gesture policy is inferred. Source WAVs are generated canonical files;
this is not a generic WAV parser or original PSND reader.

The actual game has no voice playback hook yet. AudioContext creation/output,
audible comparison, supported browsers and source dialogue timing remain untested.
The server still selects the previous v2 opening asset directory. Switching asset
packages is not an audio or playable milestone. No additional audio/debug UI was
added; eventual playback must use the original conversation/menu affordances.


The bounded navigation rule check is now available:

```sh
bun tests/test_browser_navigation.ts
```

It matches1,231 common and302 ticket-office original-instruction outputs, including cached-frame sprite
interception cases. The source-population, padding, clock and activation context
must be supplied explicitly. Actual scenes must not be represented by a guessed
empty sprite list or a visibility-only filter. The current opening does not yet
connect navigation; this check is a prerequisite, not a browser playtest.

Ticket and boarding rule verification:

```sh
bun tests/ticket-oracle.ts
```

This compares4,826 original contexts and seven original TREE graphs; UI, delayed
countdown completion and voyage entry remain unimplemented. The independent
experimental emulator trial is described in BROWSER-EMULATION-EVALUATION.md.
Its canvas-only adapter and optional server mount are prepared but have never
executed a guest or backend. It does not replace the current native opening.
