# Execution checkpoint

Updated: 2026-10-14. Current phase: verified source recovery, a running
original-game reference, one completed blind playthrough, and selected image/sound recovery.
The M0 source/reference checkpoint is reached;
M1 now has its bounded recovery proof and runtime decision; M2 remains incomplete.
A partial local name/journal/Wharf opening is implemented and served. It has no
Seattle interaction, save/load or browser execution validation, so there is no
playable milestone or general gameplay fidelity claim. Historical bullets below
retain earlier check counts; the latest checkpoint supersedes their pending work.

## Latest implementation checkpoint

- 2026-10-14 tooling: Prettier formatting for `web/**/*.{ts,html,css}` with a
  `pretty-quick --staged` pre-commit hook via `simple-git-hooks`; `.prettierignore`
  limits it to `web/`. See RUNTIME-DECISION.md (formatting revision). Layout-only
  change; `bun run typecheck` and `bun run test` rerun after the reformat.

- 2026-10-14: converted the web port to TypeScript and Vite at the owner's
  request. All `web/**/*.mjs` and `tests/*.mjs` are now `.ts` (git renames);
  rule modules carry interfaces for recovered vocabularies/state/buffers and
  keep every runtime guard. `package.json` scripts: `dev`/`build`/`preview`
  (Vite 8.3.4), `typecheck` (TypeScript 7.0.2, strict for `web/`, relaxed for
  tests), `test` (`tests/run-oracles.ts`). `tools/serve_port.py` and its test
  were replaced by `tools/selected-assets.ts`, a Vite dev/preview mount for
  `YUKON_ASSETS`/`YUKON_TRIAL_ASSETS` with the same fail-closed path rules and
  a ported boundary test (`tests/test_selected_assets.ts`). Checks run: both
  typechecks clean; 20/20 self-contained checks pass under Bun 1.3.14 and
  Node 26.0.0; the eight local-input oracle checks and the pinned emulator
  contract check pass; `vite build` succeeds; dev and preview servers on
  127.0.0.1:8000 serve `/`, `/emulation-trial/`, `/game-assets/manifest.json`
  (SHA e48de289…) and return 404/403 for traversal, unmounted and `/@fs/`
  paths outside `web/` (curl checks).
- 2026-10-14: first actual browser execution of the port. Chrome (via the
  browser tool, previously denied on this origin) loaded the Vite dev origin,
  rendered the Wharf background, name dialog, journal view with source font
  and three inventory overlays, and then threw
  `Source pose and imported actor frame geometry differ` on Done. Cause: a
  pre-existing off-by-one in `web/main.mjs` (HEAD line85) that compared an
  inclusive `+1` extent against `frameRectangle`'s exclusive bottom/right,
  which the native population oracle confirms (`[218,86,387,158]` for a
  72×169 frame). Fixed to compare `right-left`/`bottom-top`; after the fix the
  Wharf paints the three recovered actors with no console errors. This is a
  one-flow smoke check, not a presentation comparison against the original;
  DPI, font metrics, scrollbars and Edit behavior remain unverified.
  AGENTS.md still says no language is chosen and needs the owner's update.
  Next: compare the rendered opening against original captures.

- Inventoried all510 TREE resources;509 nonempty graphs structurally parse,
  emptyTREE39 is an explicit exclusion. Native original response graph/copy
  comparison now covers all509/2,400 response nodes/10,479 allocations with
  zero mismatches; initial roots come independently from source sentinels.
  Corpus contains1,894 choices/126 overrides and references761 nonzero voices,
  all present. Numeric action/condition references remain unassigned where
  recovery is incomplete. No UI/condition/action/override-loading proof inferred.
  Exact source IDs/hashes/limits/reproduction: formats/TREE.md and two census
  evidence reports. Standard-library synthetic census/root tests added.
- Latest completed root verification after census integration: **196 Python
  tests passed**; projection/status/navigation/ticket Node original-oracle checks
  pass, updated Python tools compile, source/generated/Ghidra artifacts remain
  ignored and `git diff --check` passes. All509 census/native resource identities,
  record counts and response totals were independently cross-checked. The active
  actor/voyage/alternate-journey workers have separate unfinished boundaries.
- User-requested attempt to reopen Chrome at a blank tab returned
  `Browser is not available: chrome`. No navigation to the blocked site through
  another surface. In-app origin denial still prevents browser/playtest claims.

- Integrated recovered current-status caching and all16 inventory selectors into
  the local opening. Inputs are a0x314-byte explicitly bounded known-word
  projection, not a fabricated complete world/save. Deterministic values match
  original reset; post-summary cache matches original event0→event4; overlays
  still match native024. No RNG seed/untouched allocation bytes invented.
  Main now requires source-derived journal-status vocabulary. Fresh11CBMP/
  34frame/7TREE/47voice package matches original vocabulary/table and PCM evidence;
  same127.0.0.1:8000 server switched to `seattle-journal-status-20261014`.
  Server session27654 started successfully; no HTTP/browser execution check.
  Reproduction and superseded package warning: PORT-RUN.md.
- Journal worker finalized147 full-buffer and1,584 inventory-selector original
  comparisons; seven annotations survive fresh reopen with auditSHA
  `4b0c087938b52e3e7bfcae9eadbe3e356088f0231484d4a278d31f625cc99893`.
  Bounded dirty gating/header exclusions/Edit request and overflow limitations
  are in JOURNAL-STATUS.md. Actor/controller initial population recovery is now
  assigned to that worker; actual scene hit lists remain unavailable.
- Browser retry after user reported closing Chrome again received the same
  saved-origin preference denial. No alternate surface or indirect execution.
  Continued source integration and original constrained playtests safely.
- Post-integration checks:189 Python tests, projection/asset-original comparisons,
  all147/1,584 journal cases, fresh47voice PCM and opening byte checks pass.
  Main/loader syntax passes; rendering and actual input remain untested.

- Added an experimental canvas-only trial entry at `web/emulation-trial/`, with
  pinned manifest/file identity checks, original backend frame conversion,
  physical keys, normalized pointer and source-correct left/middle/right mapping.
  Mono audio starts on a canvas gesture; pre-gesture loss/underruns are counted,
  and a backlog over two seconds stops the trial explicitly. Those are untested
  platform policies, not fidelity results. No guest/backend/browser execution,
  automatic save persistence or runtime switch. The server has an optional
  separately bounded `/emulation-assets/` mount; current running server unchanged.
  Pinned source contract checks, five server boundary tests and syntax pass.
  Reproduction/limitations: BROWSER-EMULATION-EVALUATION.md.
- Browser retry after the user reported saving an exact-origin allow exception
  still received the same saved-preference security denial for
  `http://127.0.0.1:8000/`. Authorization is already granted. No alternate origin,
  browser surface, raw browser command or indirect execution was attempted.
  Actual browser playtests remain unavailable; source recovery continues.
- Final ticket/boarding handoff matches4,826 native contexts and seven actual
  TREE graphs: fares, clerk/Wharf selection, seen marks, ship conditions and exact
  immediate/delayed boarding queues. Main integration, countdown completion,
  voyage and schedule remain open. Eleven annotations survive fresh Ghidra
  reopening. `bun tests/ticket-oracle.ts` independently rerun successfully.
- Navigation now also matches302 actual ticket-office handler contexts, in
  addition to1,231 common handler cases. The office handler has no common
  countdown gate; callers must choose the correct handler. Source annotations
  and six guarded fresh navigation-region census are finalized. Module rerun
  passes; main integration still awaits scene/journal state support.
- Current full standard-library suite: **184 tests passed**. The new trial
  adapter contract test compares against pinned vendor source without executing
  an emulator. The latest ticket and navigation Node oracle checks pass.
- Added explicit TREE corpus selection to the selected-voice native verifier.
  Seven ticket/boarding graphs now yield56 additional distinct voices,
  116,610 original integer calls and7,476,546 original PCM bytes with zero
  mismatches. Fresh native-guarded ticket package11CBMP/34frames/7TREE/56WAV
  passes independent Python export and Node voice adapter checks. Both selected
  corpora total103 distinct voices; this is not live playback or mixer proof.
  Exact identities/commands: TICKETS.md and ticket-sound-set-recovery-evidence.json.
- Source identity verifier independently rechecked the ISO and all16 selected
  extracted Windows files against direct-disc streams and recorded hashes; pass.
  Generated ticket/trial manifests and source media remain Git-ignored; JSON,
  tracked diff whitespace and new adapter file whitespace checks pass.
- Fixed an original-byte opening discrepancy: the port trimmed the original
  arrival entry's trailing space. Original event0 execution establishes the
  retained byte; updated opening check passes. Full status append/inventory
  recovery remains worker-owned and may reveal further invisible bytes. The
  opening test also matches the independently executed119-byte event0→event4
  tail exactly. Original journal UI's later WM_CHAR20 request is distinct from
  formatting and remains a presentation/state-lifecycle integration item.
- Independently inspected finalized WHITEB/WHITES original save copies: both
  exact11221-byte containers round-trip without change, cash122/bank0/food1971/
  partner4. WHITEBday28/month12/phase5 agrees with observed prebuild reload.
  WHITES has day29/month5/phase10 while preserving its last Dec28 journal; do
  not mistake cached journal text for current state during the spring popup.
  Worker observed the spring conversation replay on WHITES reload. Exact hashes,
  raw word offsets/scope: lake-bennett-save-inspection.json. No port-save claim.
- Final root checkpoint suite after concurrent recovery additions: **189 Python
  tests passed**. Opening tail, trial source contracts and syntax rerun pass;
  all documentation JSON and tracked diff whitespace pass. Workers' unfinished
  countdown/journal source recovery is excluded from root milestone claims.

- Prepared a frozen offline browser-emulation trial asset set as the documented
  fallback:837 preserved guest members/21,734,040 file bytes,14,747,472-byte ZIP,
  unchanged370,939,904-byte ISO copy and three pinned vendor artifacts. All guest
  hashes/ZIP CRC/config and original baseline/ISO identities pass. Recognized
  AppleDouble metadata is explicitly recorded/omitted; unsafe paths/types/DOS
  aliases and source drift fail. No emulator/browser execution or architecture
  switch; actual launch, pointer, sound, saves and browser performance
  remain unverified. Commands/limits: BROWSER-EMULATION-EVALUATION.md and
  browser-emulation-trial-preparation.json.
- Earlier read official OpenAI browser settings/origin policy documentation and inspected
  only local browser-policy keys: no local config.toml browser rule found. The
  user reported no matching origin rule; removal may have restored a blocking
  default. Requested an explicit browsing exception for the exact127.0.0.1:8000
  origin. No policy modification, bypass or further unapproved retry performed.
- Review caught a navigation census scope error: it assumed partnerword0 false
  for condition(3,1), but the retained native oracle says0 true and freshffff
  false. Worker corrected the census to actual freshffff and retained exact
  original condition evidence. Source-clear region integration still requires
  global anchor/no-overlay/context guards; whole-screen empty sprite lists remain
  invalid.

- Seattle button/navigation module now matches1,231 actual original instruction
  cases, including121 complete cached-frame sprite-hit/interception cases.
  Window button coordinates pass unchanged; source manager rectangle edges are
  inclusive while HSPT comparisons are strict. Sprite pixel tests use native
  stride indexing with the original width×height bound. Explicit sprite list,
  initialized padding, active globals, countdown and activation context remain
  required. Do not silently supply an empty list for a real scene. Source actor
  population and defensible navigation integration are still worker-owned;
  main.ts has not yet connected this module. Navigation evidence/module/tests
  are ready; source annotations/doc handoff are being finalized.
- Earlier ticket-clerk/fare/inventory/boarding exit recovery was assigned to the
  finished sound worker, using original observations and unchanged native code.
  Original White Pass alternate cleared customs and paid100, with aftercash122;
  it continues toward Lake Bennett. Immediate conversation journal access was
  disabled, so food/date changes are not attributed to the tax alone. Native
  input error192 was undone via original Edit→Undo; raw error capture is retained.

- Prepared a fresh selected Seattle asset package with11 CBMP/34frames,
  seven source TREE graphs and47 independently native-checked voices. Importer
  now checks optional original PCM evidence before output; a deliberately wrong
  PSND1 PCM hash fails and creates no output. Manifest retains source/PCM/WAV
  hashes and declared/consumed lengths. `web/platform/voice.ts` reads only
  canonical generated mono8-bit/22050Hz WAV and supplies an explicit AudioBuffer
  adapter; loader verifies WAV/PCM identity and returns independent samples.
  Node checks all47 voices/7,626,207 native sample bytes. No AudioContext output,
  gesture, gain, playback timing or browser fidelity claim. Reproduction and
  limits: PORT-RUN.md, browser-voice-adapter-evidence.json. Served v2 remains
  unchanged until scene/audio integration is ready.
- Sound recovery now accepts all871 source resources after original header,
  terminal-block/cursor and rare-order proofs; acceptance is not all-voice native
  or mixer validation. Selected47voice sample proof/corpus identities are in
  seattle-sound-set-recovery-evidence.json and sound-census-evidence.json.

- Follow-up save header recovery:246 actual original branch/comparison cases
  match Python and Node. Corrected an invented zero-padding restriction: original
  ignores signature byte5 and post-NUL title/version padding. Preserved those
  bytes; original lexical version/status decisions are exposed, with older-version
  restore explicitly unsupported. Source load reads buffers before validation;
  rollback and scene recreation are unknown. See formats/GAM.md and
  save-header-recovery-evidence.json. Browser persistence remains incomplete.

- Recovered the original fixed save container and added Python/JavaScript
  byte-preserving readers. Unchanged original974a/97ec plus read/write count
  wrappers transfer all five finalized evidence saves exactly through substituted
  in-memory file APIs:5/64/10/902/10240-byte blocks,11221 total. Saved raw Seattle
  values independently match the recorded restore. No browser persistence or
  full load/scene recreation claim; full error UI/global RNG dependencies
  remain open. Five saved names/comments survive fresh Ghidra reopening with identical audits.
  Exact evidence/reproduction: [formats/GAM.md](formats/GAM.md).

- Latest full standard-library run: **183 tests passed**; twelve Node
  original-oracle commands passed. `node --check web/main.ts`, parsing all
  documentation JSON files and `git diff --check` passed. Source ISO, generated
  asset manifest and native captures remain Git-ignored. Counts are checkpoints;
  active workers may add further cases before their finalized handoffs.
- Reusable journal native024 comparison now checks55,170 selected pixels with
  zero differences:38,000 cloth,4,369 frame10,7,210 unoccluded frame6 and5,591
  frame11. Source-derived positions, capture/resource hashes and explicit
  zero/clip/occlusion exclusions are in journal-capture-comparison.json and
  JOURNAL-PRESENTATION.md; no alignment search or whole-scene claim.

- Implemented the local opening in `web/`: original name prompt, source-derived
  editable journal, original font/background and three fresh inventory overlays,
  Done → Wharf, Game journal reopening/Ctrl+J. Added a loopback-only asset server,
  four path-boundary checks, and provenance-preserving asset preparation. The platform loader also exposes hash-checked selected TREE
  resources for the next integration; its browser path is unverified. Exact
  commands and unsupported behavior are in [PORT-RUN.md](PORT-RUN.md).
- Nine rule/opening Node original-oracle commands plus the new save-container
  check pass:400 money/16 eligibility,243 copy,
  36 full reset/RNG,2190 calendar/192 scene-entry,112 whipsaw purchase,
  645 hotspot/5 geometry/36 suspension,176 TREE links/18 Linda opening,
  576 journal/48 actual Seattle tuple/3 queue cases, plus opening visible-text
  and text-range checks. Font/browser events/rendering remain untested.
- Recovered full raw reset/RNG, actual Seattle location tuples and first-visit
  calendar entry, recursive TREE links/conditions, whipsaw dispatch/refusal,
  source sprite/hotspot geometry and journal controls/inventory. Each exact
  source address/hash, original execution scope and reproduction is linked from
  SEATTLE-RULES.md, SEATTLE-SPRITES.md and JOURNAL-PRESENTATION.md. Do not collapse
  these into a claim that the complete UI/action scheduler is recovered.
- Constrained original Seattle reference is finalized:101 PNGs, three fully
  decoded AVI/WAV pairs, all four selected partner introductions/cash replies,
  isolated first-Downtown date check and two SEATTLE.GAM reloads. Visible saved
  Linda/Aug24/$422/2400lb/whipsaw+outfit state is restored; save identity remains
  unchanged. Save container/header checks are recovered; full loader/port persistence remain
  incomplete. An independently
  controlled alternate Al-Ki/Skagway/White Pass original run is in progress;
  WHITE-PASS-REFERENCE.md retains bounded observations, not a completed ending.
- Natural WhitePassCity refusal is finalized: unaffordable1600lb/$240 with$222
  leaves visible date/food/cash unchanged. TREE600 voice601 maps to the exact
  Linda reply; original sample proof and recording comparison are retained in
  sound601-capture-comparison.json. Correlation0.995244/residual9.741% RMS,
  refined0.998180/6.030%; unexplained residual is not dismissed as mixer behavior.
- PSND3400/3401/3405 header22/count1 is now source-established and converted;
  3400/3405 native sample and live capture comparisons retain unexplained
  waveform residuals. Wider PSND corpus/header audit is in progress. Audio is
  not connected to the port. Browser emulation has a source-only feasibility
  evaluation; no guest bundle execution or runtime switch is claimed.
- Automatic approval review rejected CUA browser access to
  `http://127.0.0.1:8000/` as permission denied. The user subsequently authorized local preview/tests, but the retry was rejected
  because a saved browser permission preference still blocks the exact URL. The user reported clearing the preference; a further exact retry still returned
  the same block. Tool access remains unresolved despite explicit authorization. Do not bypass via another surface
  or raw browser commands. AppleScript covers original-game playtesting only.

## Completed (historical checkpoints)

- Recovered the separate raw date primitive:2,190 original-code comparisons
  across valid fixed-calendar dates, boundary counters/phases and mutation gate
  match. It belongs to an animation-timer/countdown path, not an unconditional
  navigation or Linda action. Source callbacks and pending-action exclusions are
  in SEATTLE-RULES.md;12 annotations survive fresh Ghidra reopening. Full suite
  now124 passes. Runtime journal/queue modules additionally match576/3 original
  cases with source-derived ignored vocabulary; no browser UI has been added.

- Independently inspected the constrained original Linda before024/after027:
  Aug24,$350→$850,0lbfood, unchanged date; source-derived partnership journal
  exactly matches visual transcription. Capture hashes/scope are retained in
  linda-live-comparison.json. Chose JavaScript modules/2D canvas after this bounded
  proof; alternatives and limitations are in RUNTIME-DECISION.md. First actual
  browser-compatible rule module `web/rules/seattle.ts` matches the400-case
  original money matrix hash and16 original eligibility cases in Node26.0.0.
  This is a tested rule module, not a playable browser application or M2.

- Recovered all eight postread transformation operations and all seventeen actual
  startup patterns from source instructions. Corrected earlier ACTS/ANMS/SPRT
  tag transcriptions. Full original routine execution matches the bounded model
  for1,274 registered source buffers; empty TREE39 and two large WRLD buffers
  remain explicitly excluded. Nine independent synthetic tests pass. Source
  identity, raw/normalized provenance, saved/reopened annotations and exact
  reproduction are in [formats/POSTREAD.md](formats/POSTREAD.md).
- Recovered selected Linda journal formatting and queued continuation:576 native
  formatter comparisons,3 queue comparisons and48 selected child-condition
  calls match. The model supplies no default date or calendar advance. Full
  activation/rendering and overflow retention remain under investigation;
  see [SEATTLE-RULES.md](SEATTLE-RULES.md).
- Resolved the45 Wharf edge differences with the actual unconditional background
  copy path, postdecode display-index normalization and explicit black palette0.
  All120,000 selected background pixels now match. The palette0 value is inferred
  from source/capture, not a measured GDI palette return; actor overlays and full
  composition remain separate.243 copy cases and256 normalization cases match
  native instructions; annotations persist. See IMAGE-COMPOSITING.md.
- The human explicitly authorized AppleScript/System Events fallback. Root full
  access and the original worker's escalated context can query/control DOSBox-X;
  their earlier restricted failures remain historical. Restored Windows boot,
  fresh name `seattle`, initial Aug23/$350/0lb journal and unobstructed Wharf are
  captured. A constrained independent worker now owns native UI, recording all
  interviews and immediate Linda before/after. Navigation to the ticket office
  already shows Aug24 before recruitment. No complete operation comparison is
  claimed while the worker is still recording; capture identities will follow.

- Started the requested full-port goal; added [COVERAGE.md](COVERAGE.md) to
  separate discovered original content, recovery checks and pending port cases.
  Human review remains due at the playable Seattle milestone. There is no
  runnable port or runtime decision yet, and the goal remains active.
- Audited all331 CBMP resources /1,523 frames with the unchanged bounded decoder:
  all accepted, no unsupported headers or dimensions found. Added reproducible
  `tools/audit_bitmaps.py`, retaining geometry, payload/index hashes and explicit
  failure reports. This is acceptance coverage, not native rendering validation.
  Full ignored census and versioned summary identities are in
  [bitmap-census-evidence.json](bitmap-census-evidence.json).
- Visually identified the four selected Seattle backgrounds; compared the
  ticket-office CBMP3000 and seven-frame CBMP4001 with original integer code:
  7,830 calls /5,406 unique, zero mismatches. The first sandboxed Unicorn run
  returned SIGILL as previously documented; approved bounded execution passed.
  CBMP4000 top600×200 at native capture origin20,59 matches119,955 pixels;
  45 index0 pixels at sourcex0 appear black and remain an open draw-path issue.
  Added exact rectangle comparison and independent synthetic cases. Full suite
  **91 tests passed**; all16 Windows files matched fresh direct-disc reads.
  [formats/CBMP.md](formats/CBMP.md) records reproducible commands and limits.
- Independently traced TREE1's first insufficient-funds response through the
  original dialogue/cache/sound dispatch to PSND1. Nine nonrelocated routing
  instructions match direct executable bytes. Four supported names/comments
  persist after fresh Ghidra reopening with byte-identical audits. Exact speaker
  and live trigger/playback remain pending; [formats/PSND.md](formats/PSND.md)
  records the evidence and similar voice branches, without claiming a live match.
- Recovered a bounded Linda acceptance/money model in `tools/yukonseattle.py`.
  Original setter/money instructions match six independent expected transitions
  and a400-case differential boundary matrix; seven synthetic tests pass.
  Four annotations survive fresh Ghidra reopening. [SEATTLE-RULES.md](SEATTLE-RULES.md)
  records source action bytes, widths, signed arithmetic, gated mutations and
  excluded journal/date/eligibility effects. The only native stub is an optional
  display-cache lookup returning null; arithmetic and setters execute unchanged.
  This is not a full dialogue operation or live before/after comparison.
- Established mode-specific normal/reverse excluded-index copy kernels and
  zero-key wrappers:162 original-code synthetic buffer cases pass. Nine supported
  names/comments persist after fresh reopening. [IMAGE-COMPOSITING.md](IMAGE-COMPOSITING.md)
  records the unconditional-copy alternative, postdecode index normalization and
  selected CBMP1/2 bubble chain through the actual manager destination table to
  source index-zero exclusion. All256 input indices match original normalization
  instructions; `tools/yukonrender.py` exposes that transform explicitly while
  preserving lossless exports. Full bubble pixels/text and the45 Wharf differences
  remain unverified. No universal CBMP alpha rule was added.
- Inspected a derived native voyage frame at nominal70 seconds: Linda and exact
  TREE616 storm text are visible. CBMP1 bubble at40,234 matches all6,317 border
  pixels; exterior/interior still excluded. Original AVI hash matches the
  preserved blind-run identity. PSND616 is therefore a concrete sound lead in
  an existing407.744-second recording; its raw header differs from PSND1 and
  order1/final partial-block support require original consumer checks before
  extending the decoder. Reproduction/metadata are in formats/CBMP.md.
- Recovered PSND616's source-mapped Linda storm voice from the recorded voyage.
  The memory/file stream getters leave record byte1 uninterpreted on this path;
  512 original getter cases, all1,284 integer calls and82,134 converted samples
  match original code. Extended the bounded decoder to orders1/2 and a final
  partial block with retained padding/metadata. PSND1 PCM/WAV is unchanged.
  The native recording aligns at69.01675 seconds: correlation0.970498,
  fitted residual24.11% RMS; fractional-sample refinement gives0.989638 and
  14.36% residual without time stretching. These differences remain recorded,
  not explained away as mixer behavior. Four stream annotations/two slots survive
  reopening. [formats/PSND.md](formats/PSND.md) records scope and commands;
  full standard-library suite **101 tests passed**. No whole-audio fidelity claim.
- Prepared a safely restored, isolated original guest from the verified
  pre-relaunch baseline:1,676 member paths/types reviewed; installed EXE/source
  hashes match and current guest/config preserved. DOSBox launch succeeded, but
  CUA/Sky `getApp` timed out after667 seconds, then `getState` timed out at60
  seconds and reset its kernel. Boot and gameplay are unobserved; there are no
  new captures or interviews. [SEATTLE-REFERENCE.md](SEATTLE-REFERENCE.md) and
  [its manifest](seattle-reference-evidence.json) preserve exact artifacts and
  the next UI recovery action. Full standard-library suite now **98 passes**.
- Added [STORY-RECONSTRUCTION.md](STORY-RECONSTRUCTION.md), a detailed narrative
  of the recorded Linda/Yosemite/Chilkoot journey through its mining and
  return-home ending. Read the supplied gameplay chat and contemporaneous
  report, directly inspected ten original PNGs, and rechecked all 16
  capture/save sizes and SHA-256 hashes against the preserved manifest; all
  matched. Journal inspection adds dated voyage/trail details and preserves
  the unexplained October 3 iceberg entry as a discrepancy. This is one
  observed story path, with interpretation and unknown branches identified;
  no new gameplay, binary recovery, or port validation was performed.
  For broader story coverage, the next concrete action is a fresh Seattle
  session recording all partner interviews and destination/ship choices,
  followed by the unplayed route. Existing technical next-work order below
  remains applicable to implementation requests.
- Reverified the supplied ISO SHA-256 and durably extracted 16 selected full-game
  Windows files under `original/extracted/windows/`. All sizes/hashes match
  [the extraction metadata](windows-extraction.json); executable/archive match
  the original [source manifest](source-manifest.json). Preserved the 489-line
  ISO listing under `local/evidence/` with its hash in versioned metadata.
- Verified the supplied [Archive item](https://archive.org/details/YUKONCD)
  against the local ISO: published size, MD5, SHA-1 and CRC32 match, and recorded
  SHA-256 is unchanged. Its JSON/XML lists agree on eight files and no separate
  CUE/BIN, audio tracks or Windows system media. Source metadata and reproduction
  are in [SOURCE-PROVENANCE.md](SOURCE-PROVENANCE.md).
- Added `tools/verify_source_files.py`: all 16 extracted Windows files match
  fresh direct-disc streams and versioned metadata. It uses the same libarchive
  reader as extraction; this checks copies/identity rather than independently
  validating ISO parsing. Its tests reject bsdtar patterns as ambiguous names.
- Implemented `tools/yukonres.py` and the [index specification](formats/YUKONRES.md).
  The source-verified reader validates all 2,522 records in 21 groups and exports
  requested raw payloads with type/ID, offsets, sizes, and hashes. Five exports
  were compared against independently recorded locations; repeat manifests are
  byte-identical. Payloads remain undecoded. `TREE:39` is a valid empty record.
- Implemented a bounded read-only HFS catalog/fork inventory. Actual source:
  170 files, 24 folders including root, 99 nonempty resource forks. Mac `YUKONRES`
  (CNID 185) matches the Windows archive by length and SHA-256. No forks were
  extracted. [MAC-SOURCE.md](MAC-SOURCE.md) records geometry, hashes, primary
  format evidence, scope limits, and a fork-preserving extraction approach.
- Inventoried reference-runtime dependencies and staged verified DOSBox-X
  2026.10.01 arm64 under ignored `local/tools/dosbox-x/`. ZIP hash, CRC/path
  review, arm64 architecture, and SDL2 bundle signature checks passed. It has
  now been launched. Archived Windows 3.1 OEM media was provisioned separately
  and its published size/MD5/SHA-1/CRC32 verified. Windows boots in 386 Enhanced
  Mode (Version 3.10) with S3 640×480/256-color and SB16 drivers. A native Windows
  Media Player `TADA.WAV` capture has nonzero PCM output; this does not validate
  host listening, MIDI, game audio or PSND decoding. A pre-first-boot guest backup
  passed read-only integrity/critical-file checks. [REFERENCE.md](REFERENCE.md)
  records the environment, sources, actual checks and remaining scope.
- Installed the full game from the mounted, unchanged ISO, including its font
  and enabled audio flags. Installed `YUKON.EXE` matches the disc's size/SHA-256;
  `YUKONRES` stays on D:. First launch reached Seattle and accepted the name
  `reference`. The opening journal shows August 23, 1897, 0 pounds of food and
  $350 cash. Native PNG/AVI/WAV captures are preserved; full AVI decode and
  independent waveform-header/signal checks passed. This validates the captured
  opening only. Installed the official Win31 DOSBox-X mouse integration driver;
  pointer alignment and the journal's Done control now work. A fresh DOSBox
  process repeated the opening and reached unobstructed Seattle Wharf. The game
  was left open at that setup checkpoint, without purchases, travel or a save.
- Completed one blind subagent run as `blind`, using only original-game UI and
  in-game Help: Seattle → Dyea → Chilkoot (customs turnback and food purchase) →
  Lake Bennett → three rafting courses → Dawson → No. 5 Below Bonanza Creek →
  mining and return home. The final newspaper reports enough gold for passage
  home; Claims of Fame records Stampeder, 14,586, July 6, 1898. One save, no
  reloads or optimization restarts. [BLIND-PLAYTHROUGH.md](BLIND-PLAYTHROUGH.md)
  records decisions and native captures. This establishes one reachable ending
  in the original, without a port comparison or alternate-route coverage.
  Independent journal/ending PNG inspection and full decode of all three run
  AVIs passed; ISO, archive, installed EXE and config SHA-256 values are unchanged.
  Claims of Fame Done returned to a fresh name prompt, left unconfirmed.
- Staged official Ghidra 12.1.4 and Temurin JDK 21.0.12.1+1 locally and imported
  the verified NE executable into `local/ghidra/YukonTrail.gpr`. A separate
  headless JVM reopened the saved program and verified a persisted source
  stamp; import/reopen audits were byte-identical. Raw NE header facts and
  Ghidra mappings are recorded in [ANALYSIS.md](ANALYSIS.md). The six imported
  libraries include `GDI`, which was omitted from the initial notes. Built the
  missing macOS native components with official Gradle 9.7.1 and existing Apple
  clang 16.0.0; a read-only startup-function decompilation completed. Its warnings
  and unresolved segment/register values are documented as tool limitations.
- Traced original archive opening, header/index reads, type/ID search,
  length/file-slice queries and record reads. The executable confirms the
  `0x58` header, 8-byte groups, 14-byte entries, and field byte swaps. The
  disassembly-derived lookup selects the expected physical row for all 2,522
  present keys and returns absent for 43 missing keys. This is static source
  consistency, not runtime fidelity. [ARCHIVE-CONSUMERS.md](ARCHIVE-CONSUMERS.md)
  records NE/Ghidra/source addresses, widths, signedness, callers and checks.
- Persisted eleven supported names/comments, four partial observed structures,
  and two bounded function boundaries in Ghidra. A fresh-process reopen retains
  all 47 annotation records and identical assembly/lead exports. Found CBMP
  buffer and PSND file-slice/buffer consumer leads; payload format and a postread
  transformation remain unresolved.
- Resolved the postread no-match behavior: NE `0001:8462` searches a
  startup-registered tag/pattern table; the17 observed registrations exclude
  CBMP and PSND. Their selected raw payloads can proceed to consumers unchanged
  on that path. The full pattern interpreter for other types remains pending.
- Added `tools/yukonbmp.py`: source-verified, bounded positive-dimension CBMP
  decoder for algorithm3/flags1. CBMP1 and CBMP2 are557×117 speech bubbles,
  with exact declared bit consumption and expanded sizes. Recovered frame
  records, MSB-first integer coding, palette subsets, block references/repeats,
  column-major8×8 tiles, and the embedded executable RGB palette.
  [formats/CBMP.md](formats/CBMP.md) documents source addresses, scope and commands.
  All 679 integer-reader calls match bounded execution of the original x86
  routines. CBMP2's6,230 border pixels match the native ending PNG at 50,234,
  zero differences after explicit palette conversion. Exterior/interior were
  excluded; full transparency/compositing is not established. The indexed PNGs
  retain source indices and palette without an invented alpha rule.
  [Versioned evidence metadata](bitmap-recovery-evidence.json) records identities.
- Added 25 independent synthetic image/capture tests and six sound tests;
  full suite 86 passes.
  Persisted 14 additional supported names/comments and two observed image
  structures in Ghidra; fresh JVM reopen retains all 40 audit records with an
  identical hash. Backed up the project before mutation. Optional original-code
  verifier uses isolated local Unicorn 2.1.4; no global runtime/package manifest.
- Recovered sequential PSND1: buffer path builds a memory stream; processor `0003:acea`
  parses record headers and packed-stream constructor `0003:b636` reads an
  algorithm3/flags2 chunk. Located block reader `0003:be0e`, subsequent conversion
  `0003:9b34`, and wave-format constructor `0003:92dc`. Implemented
  `tools/yukonsnd.py`:81,792 mono 8-bit samples at 22,050 Hz, second-order byte
  integration. All 1,278 integer calls and all converted samples/final state
  match original routines. Nine sound names/comments, one observed header layout
  and three getter bindings persist after reopening. Sequential index metadata
  is retained; seek/loop behavior remains unsupported. No convincing match in
  the two existing opening captures, so live resource-to-scene mapping and clip
  comparison remain pending. [formats/PSND.md](formats/PSND.md) records evidence,
  source addresses, scope and reproduction.
- Recorded [audio evidence](AUDIO-EVIDENCE.md): bonus-track text, installer
  flags, waveform/sequencer strings and API imports. These do not establish
  CD audio use, sample format/rate, or missing in-game music.
- Reviewed primary examples of AI-assisted game reverse engineering and documented applicable practices.
- Added documentation, agent guidance, and Git exclusions for local source material and generated work.

## Not yet done

No completed general image/compositing recovery, whole-audio fidelity,
full gameplay recovery, playable browser port, or
original-versus-port playthrough comparison. One original blind run reached an
ending; the White Pass alternate is in progress, other endings and port save/load remain
unvalidated. Guest backup/restored boot and one original Seattle save restoration
are checked; later restore boundaries and the save schema remain unvalidated. No Mac extraction/restoration or Mac original-game execution. No
Ghidra MCP integration has been evaluated; the current project uses reproducible
headless scripts. Tooling success does not establish recovered behavior.

## Next work, in order

1. Continue source-backed Seattle integration: load normalized scene resources,
   connect observed navigation/first-visit date behavior, sprites/hotspots and
   TREE dialogue/action dispatch. Preserve unsupported conditions/actions rather
   than inventing defaults. Recover ticket/exit and save schema before M2 exit.
2. When browser access is authorized, verify the current opening and source font
   in the actual browser. Assign independent blind and constrained port tests
   with separate input ownership; no port UI playtest has occurred yet.
3. Continue the worker-owned original White Pass alternate and targeted refusal
   capture. Do not race DOSBox UI or hash unfinished recordings. Preserve original
   odd journal entries rather than correcting them by assumption.
4. Complete supported sound-header/native checks and source-mapped live residual
   investigation; retain seeking/looping/mixer exclusions. Persist reusable
   journal inventory comparisons and assess source-only browser-emulation trial
   feasibility without bypassing denied browser access.
5. Request human review once the actual Seattle loop, exit and save round trip
   are playable and compared. Continue complete journey/alternate paths and
   supported-browser/save validation afterward. Public deployment remains separate.

See [milestones and exit criteria](ROADMAP.md) and [PORT-RUN.md](PORT-RUN.md).
M0 and the bounded M1 proof/decision are recorded; M2 remains incomplete.

## Open inputs and decisions

| Item | Current state | Work that can proceed |
| --- | --- | --- |
| Internet Archive item URL and download metadata | Owner-supplied item verified; download date unknown | Source work and binary analysis |
| Separate CD audio tracks | Bonus tracks 2–18 are absent from this item's listing; in-game dependency unknown | MCI/waveform consumer investigation |
| Reference system media and emulator setup | Windows 3.1 OEM/DOSBox-X works through one original-game ending; pointer/relaunch checks pass | Targeted runtime comparisons, static analysis and decoders |
| Mac executable/resources | Catalog/forks inventoried; shared archive identical; not extracted or executed | Windows work and selective evidence extraction |
| Runtime | JavaScript modules /2D canvas; alternatives documented | Actual Seattle slice and original-oracle rule checks |
| Project license and asset distribution | Undecided | Local tooling and documentation |

## Actual checks and reproducibility

- Python 3.14.5: `python3 -m unittest discover -s tests -v` — **124 tests passed**, including
  new postread, journal and selected-condition checks, requiring
  no original media. Source tests use `bsdtar` with small synthetic containers.
  Independent review found two HFS malformed-input gaps; overlap/root-parent
  checks and regression cases now pass.
- All 16 selected Windows files match their recorded sizes/SHA-256. The HFS
  command reverified the ISO identity after extraction/inspection; it is unchanged.
  This follow-up also checked each extracted file against a fresh `bsdtar -xOf`
  stream from the source ISO. Published Archive identity fields match the local
  disc; the item listing supplies no Windows guest/installer or separate tracks.
- Real archive: 2,522 records, 21 groups, index end `0x8aec`, no positive-length
  payload overlap, preserved zero-length record. Five raw exports match direct
  source reads. Reordered/repeated export requests produce the same manifest
  SHA-256 `d98715323b98c2cec6de7c5b305baa814ceb5f78fd861c1400019e6c754af3e7`.
- Real HFS: bounded catalog/fork inventory and independent absolute-region hashes
  agree; Mac archive equals Windows. Bitmap consistency, catalog index-node
  ordering and thread consistency are outside the verified scope.
- Ghidra save/reopen: source stamp retained; 261-record pre/post audit identical,
  SHA-256 `3409aff9de70666643c368faf4e3c9d0eb11fc4cd3ea33326fce6e7a9402ea93`.
  A later baseline audit adds two `YUKONRES` string locations (263 records); two
  fresh-process read-only exports are byte-identical, SHA-256
  `b4e1eecf3bdb6733616ce895200004312a1ebc35d1c66e323e3625392b3656e2`.
  Their exact-address xrefs were zero; subsequent consumer tracing follows
  segmented pointer construction instead of those automatic xrefs.
  Native build and decompiler smoke passed; auto-analysis function counts and
  pseudocode are tool output, not recovered-function fidelity.
- Original-reader verification: 2,522 present + 43 absent queries, zero static
  mismatches. Sixteen nonrelocated instructions match independently read source
  bytes. Eleven names/comments and four structures persist; 47-record annotation
  audit SHA-256 `1ea63c8bbf30ef063e05805f0c993f5b00b1f84260934cfb4e7e7c2af90c37fa`.
  Reopened assembly/lead exports also match. Runtime DS and method dispatch remain
  unobserved, and default decompiler parameter signatures remain unverified.
- Reference guest: observed Windows 3.10 in 386 Enhanced Mode; native 640×480
  screenshot and configured 256-color S3 driver. Windows waveform test capture:
  36.861 seconds, 48 kHz, 16-bit stereo, peak 4,583; independently parsed and
  hashed. Pre-first-boot backup: 1,630 entries, all paths/types checked and five
  critical Windows/driver files readable; restored guest boot was not tested.
- Original-game capture: installed executable independently matches source;
  full first-launch AVI decoded with FFmpeg 8.1.2 without errors (640×480 ZMBV,
  314.282 seconds). Separate game WAV has 314.676 seconds of 48 kHz/16-bit stereo
  output with peak 8,243. These are emulator output parameters, not recovered
  PSND source parameters. No host listening or full gameplay comparison was done.
- Repeat run: fresh DOSBox-X process, blank name prompt accepted `reference`,
  same initial journal, Done dismissed it and Seattle Wharf rendered. Official
  Win31 pointer integration fixes automation alignment. Both native game AVIs
  fully decode without errors. Repeat WAV has 362.696 seconds and nonzero PCM;
  visual captures, source/config hashes and baseline identities are recorded in
  [the reference manifest](reference-environment.json).
- Blind run: about 89 minutes, one save and zero reloads, return-home newspaper
  and Claims of Fame 14,586/Stampeder. Four terminal PNGs independently inspected;
  all three run AVIs fully decoded with FFmpeg 8.1.2 without errors. All 16
  capture/save manifest identities match; media and saves remain ignored. Source
  ISO/archive, installed EXE and config hashes are unchanged. Exact choices,
  capture hashes, decoder commands and scope are in
  [BLIND-PLAYTHROUGH.md](BLIND-PLAYTHROUGH.md).
- Tools, source metadata, specifications and synthetic tests are versioned;
  source media, raw exports, tool distributions, projects and logs remain ignored.
  Tracked/untracked whitespace review, documentation links, JSON metadata,
  launcher shell syntax and ignored-artifact checks passed. No application
  dependencies/framework/CI were added.
- Selected image proof:679 native integer calls,165 unique inputs/positions,
  zero byte/cursor mismatches. CBMP1/2 exact packed bit counts14,478/14,688,
  expanded size 67,200 each. CBMP2 capture border6,230 pixels, zero mismatches;
  11,610 exterior and47,329 interior pixels excluded. Decoder/capture scripts
  are reproducible; metadata and source/capture/output hashes are versioned.
  Ghidra recovery annotation audit 40 records, saved/reopened identical SHA-256
  `4c991e0edc75ec5e4d73751b3ca64400f063af8ae854b893b072b85ae526fa5a`.
  Source EXE/archive/ISO remain unchanged; generated assets and analysis dependencies
  remain ignored. Native verifier's Unicorn mapping requires approved execution
  outside this host sandbox; no host security settings were changed.
- Selected sound proof:1,278 integer calls and81,792 sample bytes plus final
  state match original code, zero mismatches; all four integration orders also
  pass a separate synthetic native check. Mono8-bit 22,050 Hz parameters traced
  through original getters and wave-format construction. WAV/PCM/source hashes
  and validation scope are in [sound-recovery-evidence.json](sound-recovery-evidence.json).
  Sound annotation audit 30 records, saved/reopened identical SHA-256
  `932016061ab71b29fbadd04d276c594f1c9948187abc8fef251a72e0a415bab7`;
  image annotations remain unchanged. Optional waveform search uses existing
  bundled NumPy 2.3.5 and FFmpeg 8.1.2; its low peaks establish no live match.

See `WORKFLOW.md` for extraction and test commands, `formats/YUKONRES.md` for
exports, and `MAC-SOURCE.md`, `REFERENCE.md`, and `ANALYSIS.md` for their exact
commands, versions and local artifact paths. `ARCHIVE-CONSUMERS.md` reproduces
the lookup check and saved annotation verification. The Archive URL is now supplied and
verified. Windows media and the booting guest are now provisioned separately;
no Windows-media input is needed for the opening reference. Static consumer
tracing and targeted original-versus-recovered comparisons can proceed.

Browser rule handoff: `bun tests/test_browser_seattle.ts` checks the retained
original money matrix/eligibility cases. Prepare fresh ignored vocabulary with
`python3 tools/prepare_journal_assets.py original/extracted/windows/YUKONRES
original/extracted/windows/YUKON.EXE generated/browser-proof-20261013/journal.json`
(the output must not exist), then run
`bun tests/test_browser_journal.ts generated/browser-proof-20261013/journal.json`.
Node26.0.0 matches400 money/16 eligibility/576 formatter/3 queue original cases.
No browser UI, save or journey is tested by these commands. Original TrueType
font identity/naming is in FONT-EVIDENCE.md and source font-size selection is in
JOURNAL-PRESENTATION.md; browser rasterization/styles remain unverified.

Finalized constrained-session000AVI/WAV identities independently match the
reference manifest. WAV parses as48kHz/16-bit stereo,97,471,247frames,
2,030.650979seconds. Full AVI decode withFFmpeg8.1.2 exited0 with no errors (shell session61826);
this checks recording integrity, not full behavioral validation. Recordings001/002
are now finalized and fully decode; alternate-run recordings remain worker-owned.
