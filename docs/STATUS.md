# Execution checkpoint

Updated: 2026-10-12. Current phase: verified source recovery, a running
original-game reference, one completed blind playthrough, and selected image/sound recovery.
The M0 source/reference checkpoint is reached;
M1 remains incomplete and there is no port/gameplay fidelity claim.

## Completed

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

No completed general image/compositing recovery, live resource-mapped sound comparison,
gameplay recovery, framework selection, browser port, or
original-versus-port playthrough comparison. One original blind run reached an
ending; other routes, endings, and save/load remain unvalidated.
Guest-backup restoration/boot has not
been tested. No Mac extraction/restoration or Mac original-game execution. No
Ghidra MCP integration has been evaluated; the current project uses reproducible
headless scripts. Tooling success does not establish recovered behavior.

## Next work, in order

1. **Capture a selected sound in the original.** PSND1 sequential decoding,
   conversion and playback parameters are recovered in formats/PSND.md.
   Trace its resource-to-dialogue/scene use, capture that original interaction,
   and compare the clip. The existing opening captures did not give a convincing
   waveform match. If PSND1 does not provide a practical observable case, choose
   another sound only after tracing its format/parameters; do not generalize the
   bounded decoder automatically.
   Preserve NE segment:offset alongside actual Ghidra mappings; save/reopen
   annotations. The selected CBMP proof is in formats/CBMP.md; general
   transparency/clipping and other variants are follow-up questions.
2. **Use the original for targeted comparisons.** The first owner review
   setup checkpoint was Seattle Wharf, with journal/input and repeat launch
   checked; the later blind run reached a return-home ending. An existing ending
   capture now supplies a selected image comparison. Use `REFERENCE.md`,
   `BLIND-PLAYTHROUGH.md`, and the baselines for sound and a small operation
   such as a purchase with before/after state.
   Test restored-guest boot before treating a backup as a verified replay reset.
3. **Complete the bounded recovery proof.** Extend the selected image result
   as needed for compositing, finish the live sound comparison, then recover an operation such
   as a purchase. Compare rendering/audio/state with the original before choosing
   TypeScript versus C++/WebAssembly. The archive reader is only the index part
   of this milestone.
4. **Optional Mac evidence extraction.** If needed to resolve a concrete question,
   export selected files as separate CNID-named data/resource forks with catalog
   metadata and compare output hashes against the inventory. Keep this separate
   from Windows files and retain the unchanged ISO.

See [milestones and exit criteria](ROADMAP.md) for what constitutes completion.
The source/reference checkpoint above supplies M0 evidence; M1's bounded recovery
proof is still pending.

## Open inputs and decisions

| Item | Current state | Work that can proceed |
| --- | --- | --- |
| Internet Archive item URL and download metadata | Owner-supplied item verified; download date unknown | Source work and binary analysis |
| Separate CD audio tracks | Bonus tracks 2–18 are absent from this item's listing; in-game dependency unknown | MCI/waveform consumer investigation |
| Reference system media and emulator setup | Windows 3.1 OEM/DOSBox-X works through one original-game ending; pointer/relaunch checks pass | Targeted runtime comparisons, static analysis and decoders |
| Mac executable/resources | Catalog/forks inventoried; shared archive identical; not extracted or executed | Windows work and selective evidence extraction |
| TypeScript versus C++/WebAssembly | Deferred until proof milestone | Extraction and behavior research |
| Project license and asset distribution | Undecided | Local tooling and documentation |

## Actual checks and reproducibility

- Python 3.14.5: `python3 -m unittest discover -s tests -v` — **86 tests passed**
  (23 archive-reader, 22 HFS-inventory, 10 source-verification, 25 image/capture, six sound tests), requiring
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
