# Bounded Seattle partner operation

Checked 2026-10-13. **Observed in source and isolated native execution:** the
selected Linda acceptance contributes $500 to the money slot used by the
Seattle cash display, sets partner code4, and writes state word+0x344 to1.
The independent original before/after UI comparison is finalized in
SEATTLE-REFERENCE.md and linda-live-comparison.json; this document does not claim
a complete dialogue engine or playable Seattle implementation.

## Sources and action record

Executable `original/extracted/windows/YUKON.EXE`, SHA-256
`9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`.
Archive `original/extracted/windows/YUKONRES`, SHA-256
`438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`.
`TREE:3400` contains Linda's partner interview and acceptance, archive offset
`0x528dc69`, length14,526, payload SHA-256
`948242aaa095b020ee47f6b6df71d8a4abaeedb14517ab85e6d8feb105b0e57a`.
The selected response “OK. I'll go get the tickets.”
occurs in three records at payload+0xcdc, +0x1dfc and+0x2be6. Each record has
the same eight action bytes at record+4:

```text
00 f0 00 04 00 00 01 f4
```

The source consumer supports opcode0xf0, partner word4, and amount500.
The on-disk amount occupies four bytes; the selected consumer uses its
transformed low16-bit word. The TREE word transformation is now recovered in
[POSTREAD.md](formats/POSTREAD.md); full field semantics/dialogue execution
remain unrecovered. No generalized TREE behavior claim is made here.
The code-to-text routing is described in [PSND.md](formats/PSND.md).

## Native dispatch and state writes

| Operation | Original NE | Ghidra | Source file offset |
| --- | --- | --- | --- |
| Partner dialogue action dispatcher | `0002:22c6` | `1008:22c6` | `0x11586` |
| Selected acceptance operation | `0002:23c6` | `1008:23c6` | `0x11686` |
| Set partner word | `0001:9df8` | `1000:9df8` | `0xa258` |
| Set word+0x344 | `0001:a652` | `1000:a652` | `0xaab2` |
| Mutate money slots | `0001:a184` | `1000:a184` | `0xa5e4` |

All offsets are relative to the actual segmented state object at DS:5308;
the runtime far-pointer value was not inspected. Ghidra selectors are import
mappings, not runtime selectors.

**Observed:** dialogue dispatcher compares opcode by subtracting0xe6 then10;
0xf0 reaches `0002:235a`. It pushes operation word+2 and word+4, then the
dialogue far pointer, into `0002:23c6`. At that callee, BP+0xc is partner and
BP+0xa is amount. The routine calls:

- `0001:9df8`: writes partner to state+0x312 unless state+0x334 is nonzero.
- `0001:c474` with event7 and partner: a journal/event lead, not recovered here.
- `0001:a652`: writes1 to state+0x344 for partner codes2 or4; codes1 or3
  supply0. The word's broader meaning remains **unknown**.
- `0001:a184`: amount is sign-extended from16 bits at `0002:23f7`; slot0
  is pushed explicitly at `23f5`. For Linda this is +500.

It then locates/returns through scene objects and sends an action code3.
That scene transition and journal/date behavior are outside this bounded model.
The source at `0001:9df8` and `a184` checks state+0x334 before mutation;
the flag's game meaning remains **unknown**. `a652` does not check that flag.
The routines mark another object's word+0x54 as1; this is an observed
notification/dirty-flag write, not an implemented UI rule.

## Money arithmetic subset

**Observed:** `0001:a184` accepts state far pointer at BP+6, delta dword at+a,
and slot word at+e; `RETF0xa` confirms ten explicit argument bytes. Slots are
16-bit words starting state+0x2fa, indexed by2×slot. It does not perform
32-bit monetary addition. For selected slot0:

- Positive/zero deltas add the low word with16-bit wrapping, then clamp a
  negative signed16-bit resulting slot to0 (`a266–a26f`).
- Negative deltas first add to slot0. If the signed result is negative, the
  same deficit is added to slot1 at+0x2fc. A negative signed slot1 result
  returns0 with both money words unchanged; otherwise slot0 becomes0.
- A nonzero state+0x334 bypasses the mutation and returns1.

Calling the second slot `bank` is an **inferred** interpretation of native
cash/bank paths; its address, width and arithmetic are **observed**. The model
names fields with `word` to preserve the original widths. Only signed16-bit
deltas in slot0 are implemented. Broader dword inputs and other slots fail
explicitly instead of inventing behavior.

## Implementation and independent checks

`tools/yukonseattle.py` implements only selected Linda acceptance and the
checked slot0 money subset. It rejects other opcodes, partners/contributions,
invalid words and deltas outside the supported subset. State values are
explicit inputs; no invented game defaults, date or journal are supplied.

`tools/verify_seattle_native.py` executes unchanged original instruction ranges
`0001:9df8–9e1b`, `a652–a66d`, and `a184–a27d` in Unicorn2.1.4 with synthetic
far-pointer/state memory. It composes those original setters in the observed
order; it does not execute the whole `0002:23c6` dispatcher. Only the optional
display-cache lookup at `0001:a1bd` is hooked to return a null display object
and perform its verified `RETF8` argument cleanup. No native money arithmetic
or setter is stubbed. Driver, scene, journal and date calls are excluded.

Six hand-calculated cases passed native execution and match the recovered model:
The actual report is [seattle-recovery-evidence.json](seattle-recovery-evidence.json).

| Input cash / second slot / delta / gate | Native output cash / second slot | Result |
| --- | --- | --- |
| 350 / 0 / +500 / 0 | 850 / 0 | partner4, flag344=1, success1 |
| 350 / 0 / +500 / 1 | 350 / 0 | partner unchanged, flag344=1, success1 |
| 850 / 0 / -60 / 0 | 790 / 0 | success1 |
| 20 / 100 / -60 / 0 | 0 / 60 | success1 |
| 20 / 30 / -60 / 0 | 20 / 30 | success0 |
| 32,760 / 0 / +500 / 0 | 0 / 0 | signed overflow clamp, success1 |

Nine nonrelocated dispatcher/setter instructions also match the direct source
bytes. Seven standard-library tests verify those independent expectations and
explicit unsupported-input failures. These are bounded source comparisons,
not full original-versus-port playthrough validation.

The exposed money-word boundaries were additionally compared with the original
as an independent oracle: the Cartesian product of cash/second-slot words
`0,20,32767,32768,65535`, deltas `-32768,-500,-60,-1,0,1,500,32767`, and
gate0/1 gives400 cases. All model money outputs, selected partner/flag writes
and success results match native execution; zero mismatches. The report
records the matrix inputs and a deterministic row hash. This samples every
signed/unsigned boundary listed; it is not exhaustive over all16-bit inputs.

```sh
python3 -m unittest tests/test_yukonseattle.py -v
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_seattle_native.py \
  original/extracted/windows/YUKON.EXE \
  local/evidence/recovery-proof/seattle-native.json
```

The pinned Unicorn staging is documented in [CBMP.md](formats/CBMP.md).
The sandbox's executable-memory mapping abort (exit132) recurred; the same
verifier succeeded with approved sandbox escalation. This is a host-tool
limitation, not a failing game case.

Four supported native names/comments were saved with
`tools/ghidra/AnnotateSeattleOperation.java`, then verified in a fresh read-only
Ghidra12.1.4/JDK21 JVM; the nine-line audits are byte-identical. Parameter
signatures remain unchanged. Backup:
`local/ghidra/backups/seattle-operation-before-20261013.tar.gz`. Reproduce with
the headless command style in [PSND.md](formats/PSND.md), substituting
`AnnotateSeattleOperation.java apply|verify AUDIT_PATH`. Read-only assembly/C
probes are `local/ghidra/seattle-partner-operation` and
`local/ghidra/seattle-money-operation`, exported using `DecompileSmoke.java`
at `1008:23c6` and `1000:a184`. Disassembly/native results are the basis;
guessed decompiler types are not installed.

**Next check:** compare a freshly recorded original journal before/after the
selected Linda confirmation, then bind the captured $350→$850 and partner/date
evidence to this operation. Recover date and journal side effects separately
before treating the entire partnership flow as implemented. Yosemite's raw
ticket record `TREE:3550` at+0x5afe contains opcode0xfa, ship252, amount60;
its eligibility/flag mutations are a separate, unimplemented lead.

## Follow-up: selected Linda journal and pending continuation

**Observed in the verified original executable and native instruction execution:**
`0001:c474` selects event7 at `0001:c7e8`, loads `CSTR:505` at `c838`,
then builds an entry with `0001:d364` (separator), `0001:cdae` (date),
`0001:cff8` (place) and `0002:2040` (partner string at index partner−1).
The selected fourth string describes Linda's contribution. Resource identity:
archive offset `0xbe0b39` (12454713), length522, SHA-256
`3aa310d5dc68ffc9618ae3085294b5b43548a1d527b97a04b277bfab5b941e2a`.
The raw resource begins with BE count4 and four NUL-terminated strings. The
independently verified startup postread transform changes the count word only;
see [POSTREAD.md](formats/POSTREAD.md). Original prose stays in source assets.

The executable identity remains the SHA-256 recorded above. NE segment1 maps
as Ghidra `1000`, segment2 as `1008`, segment6 as `1028`, data segment13 as
`1060`; original file starts are respectively `0x460`, `0xf2c0`, `0x44fc0`
and `0x4f420`. The model reads the following bounded strings from data13:
month names at `0f2e,0f37,0f41,0f48,0f4f,0f54,0f5a,0f60,0f68,0f73,0f7c,0f86`,
year suffixes `0f90/0f99`, Seattle `0fa2`, separator parts `1093/1096`.

`0001:a68e` reads state words `+28` (day) and `+2a` (month). The formatter
appends the source month string and decimal day. `0001:a850` reads `+310`;
the date formatter compares that **signed** word to5, choosing the source
1897 suffix for ≤5 and 1898 otherwise. This is the observed formatter switch,
not a recovered calendar or the meaning of `+310`. `0001:a6f4` reads location
words `+34/+36/+38`; this implementation supports only `(200,0,0)`, which
selects the Seattle string. An existing nonempty journal adds CRLFCRLF before
the entry. Each component is appended only if the combined entry length is
strictly less than255, excluding the terminating NUL. Main journal append at
`0001:cb01` accepts a combined length below `0x2800`; the overflow/drop path
is not implemented and fails explicitly. These getters and formatting routines
do not write the game-state date words.

`tools/yukonjournal.py` implements this selected formatting, source vocabulary
loading and non-overflow concatenation. `accept_linda_effects` in
`tools/yukonseattle.py` composes the established setters/money result, journal
entry and pending continuation using explicit date, journal and manager inputs.
It does not create a game state or advance the date.

**Observed continuation, partially recovered:** after the partner setters,
`0002:23c6` climbs the scene-manager parent chain (`0001:3e6a`) to kind200,
calls `0002:0f92`, then queues action3 at `0001:4dba`. The latter copies
`03 00 00 00 00 00 00 00` to manager bytes `+4..+11` and sets word `+2=1`,
preserving other bytes. `0001:3c7a` later handles action3 via `0001:4ba8`
(pop one active scene for the selected argument0), shifts the scene stack,
and sends the remaining scene virtual messages `046b` and `0465`. This is
more specific than an assumed direct navigation to a scene ID.

**Unknown:** `0002:0f92` deletes/recreates a controller at object `+4c` through
`0003:2268`, then calls `0003:26f2` with flag1. Its constructor/activation,
subsequent scene callbacks, and any date effects of those callbacks remain
unrecovered. Queueing is implemented; controller activation and processing the
scene stack are excluded. A full original before/after acceptance capture is
still needed to establish the end-to-end operation. The previously recorded
$350→$850 observation alone does not prove these additional effects.

**Independent checks:** `tools/verify_journal_native.py` executes original
separator/date/place/CSTR-selector/string instructions in Unicorn2.1.4, using
checked synthetic far-call relocations and explicit state/context. It compares
576 combinations (12months × days1/9/24/31 × phase words0/5/6/32767/32768/65535
× empty/nonempty journal) to the model: zero mismatches and no state writes.
It also executes original string concatenation for the selected non-overflow
append and original `0001:4dba` queue/copy against three sentinel buffers.
Expected results come from original instructions. Metadata and all checked
relocation sites are in `journal-recovery-evidence.json`; bulk original text
and disassembly remain ignored. One source internal-entry relocation at
`0002:205e` targets runtime `0006:1f88` despite placeholder operand offset
`1b86`; this offset relocation is explicit, not a guessed alternate function.
Allocator/full event dispatcher, overflow retention and UI activation are not
emulated in this verifier. Eight synthetic unit tests cover malformed inputs,
capacity boundaries, signed phase comparison and exact queue writes.

Reproduction from the repository root (Python3.14.5; existing original assets):

```sh
python3 -m unittest tests.test_yukonjournal tests.test_yukonseattle
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_journal_native.py original/extracted/windows/YUKONRES \
  original/extracted/windows/YUKON.EXE docs/journal-recovery-evidence.json
```

Unicorn's executable-memory mapping requires the same narrow sandbox approval
as the other original-code verifiers. Read-only bounded disassembly can be
re-exported with `ProbeJournalCase.java` and `ProbeJournalHelpers.java` against
the pinned Ghidra12.1.4 project; coordinate exclusive project access.

**Further source/native continuation evidence:** `0003:2268` / Ghidra
`1010:2268` installs method table `0006:78d2`, saves owner at `+1e`, loads
`SCRP` at the ID supplied by owner `SCNE+6`, then calls `0003:2394`.
Normalized `SCNE:4000` has word `+6=4000`; therefore this selected source scene
uses `SCRP:4000`. The latter's raw archive offset is85717655 (`0x51bf297`),
length290, SHA-256
`898c985d0c422471f3cc64caaf78f8458cf16d5024c0f788c0076e691140dfcb`.
The controller consumer uses a countword and18byte records; `SCRP:4000`
has16 records. Three four-byte condition pairs per record are evaluated by
`0003:5118`; only a conjunction creates that child. Kind3 reads a `SPRT`
resource and constructs an associated object. This establishes a selected
resource consumer, not a general script VM.

Record15 (zero-based, normalized byte272) is kind3/SPRT403 and has condition
pairs `(3,1),(5,4),(0,0)`. Original condition3 checks a signed nonnegative
partner word for argument1; condition5 tests equality with partnerword4;
condition0 returns1. Both partner branches read state`+312` through
`0001:a632` (Ghidra `1000:a632`). Thus the conjunction selects the Linda
child when partnerword4. `linda_scene_child_eligible` implements only this
selected conjunction; it does not create or draw the child. Native execution
of the original condition routine and getter covers16 partnerwords spanning
0..9 and signed boundaries32766/32767/32768/32769/65534/65535 (48calls), with
zero model mismatches and no state writes. Calls at `0003:5763` and `5969`
are relocated to synthetic code selectors, with original instructions intact;
see `linda-child-recovery-evidence.json`.

`0003:26f2` traverses the controller child list (`+0c`, nextfar`+8`). For
kind3 it writes argument1 to associated target object word`+84`; argument0
would also set targetword`+82=1`. The meaning of those flags, remaining
condition branches and sprite object behavior remain unknown. No calendar
call appears in the observed constructor, selected condition or flag-setting
paths; this does not establish that later scene activation never advances time.

Nine supported function names/comments in `AnnotateJournal.java` were saved
and freshly reopened, with identical audit SHA-256
`e64cad5c0fb57f550a3840edeff2738df880647110a1dbb15c539ad93f9c74a7`.
No guessed parameter signatures were installed. Backup:
`local/ghidra/backups/journal-before-20261014.tar.gz`. Reproduce the annotations
with the documented headless `apply|verify` command style. Useful ignored
read-only exports are `linda-controller-create`, `linda-controller-populate`,
`linda-controller-activate`, `scene-condition-evaluate` and
`condition-getter-a632`. The full condition decompiler output has overlapping
instruction warnings: selected original instruction execution and disassembly,
not those inferred types, support the bounded result.

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_linda_child_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/linda-child-recovery-evidence.json
```

**Next concrete recovery:** trace the active Seattle scene's `0465/046b`
callbacks and kind3 `SPRT:403` constructor/draw/flag consumer. Compare the full
acceptance against a live original before/after journal and scene capture when
original UI access is restored. Do not treat the journal/queue/eligibility
checks as complete end-to-end Linda operation validation.

## Independent immediate original comparison

The constrained original worker captured before024 and after027 around Linda's
acceptance with no intervening spending or travel. Root independently inspected
both PNGs: August24,1897 Seattle,0lbfood,$350→$850; the partnership entry
visually transcribes exactly to the executable/CSTR formatter result. Its byte
SHA-256 is `b63718773929b4f68542f6c734f79c39347acade99cba7f616c5615407ee57b1`.
[The comparison report](linda-live-comparison.json) retains capture hashes,
observations and scope. Reproduce the derived entry with `source_vocabulary`,
`linda_entry(vocabulary, raw_CSTR505, 24, 8, 0, b'')`; load CSTR505 at the source
offset/length above. This checks visible text/money/date, not hidden memory or
full activation. An initial failed keyboard probe inserted blanklines into the
editable journal before the immediate baseline; this did not change observed
money/food/date. Earlier Seattle navigation advanced Aug23→24 before recruitment,
so acceptance itself must not acquire an invented date advance.

## Follow-up: activation messages and a separate day-increment routine

**Observed source dispatch:** the scene constructor `0002:0002` installs
method table `0006:6646`. Its message slot`+4` points to `0002:0c72` / Ghidra
`1008:0c72`; this is confirmed by the source NE segment6 segment-only
relocation chain entry8 at`664c` (target segment2) and raw offsetword`0c72`
at`664a`, then the reopened Ghidra table. Full bounded disassembly was initially
missing and is now saved through `AnnotateJournal.java`.

The Linda action3 scene-pop dispatcher sends **046b then0465**, as recorded
above. Their direct effects are:

| Message | Native branch | Observed operation |
| --- | --- | --- |
| `046b` | `0002:0e98` | Restore saved sprite-list far pointer `scene+54` to global manager DS`0094` object`+48`; copy background CBMP `scene+50` through manager slot`+20`; call controller `0003:26f2` with0; optional animation targetword`+70=0`; two scene objects at`+3c/+38` targetword`+8a=0`; call `0001:47d8` with scene cursor/resourceword`+42`. |
| `0465` | `0002:0e1c` | Call window/GDI refresh `0001:607e(flag1)`, scene slot`+8`→`0002:0f62` (pause a separate animation if present), then `0001:59dc` (window/GDI release). |
| `046a` | `0002:0e40` | Save the manager sprite list to `scene+54`; controllerflag1 and corresponding targetword`+70/+8a` flags1. This branch is distinct from0465. |

The manager DS`0094` table`0006:706a` slot`+20` maps to background copy
`0002:3ee2`, already traced to the unconditional original image-copy path in
[IMAGE-COMPOSITING.md](IMAGE-COMPOSITING.md). The scene's`+50` comes from the
normalized SCNE firstword CBMP request at`0002:0353–038a`; `+54` stores a
sprite-child-list snapshot. These are observed presentation fields, not date
words. `0003:26f2(flag0)` also sets kind3 targetword`+82=1` and `+84=0`;
flag1 sets`+84=1`. The kind3 update consumer is being independently recovered;
these flags must not be silently treated as visibility.

**Explicit pending-action dependency:** after recognized messages, common
code at `0002:0df7` checks scene word`+0e`. If nonzero, it clears that word and
passes the stored eight-byte action at`+10` to virtual slot`+10`→`0002:0890`.
That scene action handler can queue further scenes or start an animation.
No assumption that this pending payload is zero has been added to the Linda
operation. The direct046b/0465 branches contain no date getter/setter calls;
this alone does not prove that every full callback execution has no state
changes, because the pending-action branch must be bound to the actual context.
Window/GDI, cursor/resource effects and full callback execution are not
included in the native state proof below.

**Separate observed day advance:** `0001:a0c2` / Ghidra `1000:a0c2`, source
file offset`0xa522`, is now implemented by `tools/yukoncalendar.py`. It takes
explicit `DateWords`: state day`+28`, month`+2a`, elapsedword`+30e`, raw
phaseword`+310`, gate`+334`. A nonzero gate suppresses all mutations. Otherwise
it increments the elapsedword and day, uses the original fixed month lengths
`31,28,31,30,31,30,31,31,30,31,30,31`, and on month overflow sets day1,
increments month (12 wraps to1), and increments raw phaseword. Counter and
phase increments wrap16bits. The original routine marks separate global
DS`52fc` object word`+54=1`. Valid original month/day ranges are supported;
invalid dates fail instead of reproducing an unchecked native stack lookup.
The implementation supplies neither a default start date nor a year/leap rule.

**Observed caller constraint:** `0002:0740` calls the date routine at`07a4`
only when scene animationfar`+18` is nonnull and signed global DS`1188`
countdown is positive. It updates that animation, increments the date,
decrements the countdown and returns. When the countdown is exhausted it
cancels animation/timers and queues the next action. The scene message handler
invokes `0740` for message0466 only if the scene is the manager's active top
scene and the timer ID matches scene word`+1e` (`0f1a–0f3a`). Thus a day
increment belongs to this animation/timer path, not automatically to every
navigation or Linda acceptance. The live Aug23 arrival and Aug24 pre-interview
journal are comparison leads; exact original input/timer binding remains to
be recorded.

**Native verification:** `verify_calendar_native.py` executes unchanged
`0001:a0c2` original instructions and dirty notification, with explicit state
and a synthetic dirty-object pointer. No behavior or platform calls are
stubbed. All365 valid fixed-calendar dates × three elapsed/phase pairs
`(0,0),(32767,5),(65535,65535)` × gate0/1 give2190 comparisons, zero
mismatches, including full-state sentinel preservation. Metadata is in
`calendar-recovery-evidence.json`. Five unit tests cover the August23→24
primitive, original February rollover, December/counter wrap, suppression and
invalid inputs. These verify the primitive independently of a UI caller.

```sh
python3 -m unittest tests.test_yukoncalendar
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_calendar_native.py \
  original/extracted/windows/YUKON.EXE docs/calendar-recovery-evidence.json
```

**Remaining selected-operation proof:** bind pending scene action`+0e/+10`,
animation`+18`, countdown and timer IDs to the original acceptance context;
verify live before/after journal/date and scene. This follow-up narrows the
source transition and implements the real day primitive, but does not claim
full callback/platform fidelity or complete Linda-operation validation.

The expanded12-function annotation set was saved and checked in a fresh
Ghidra12.1.4/JDK21 process; apply/reopen audit SHA-256 is
`ad13af576605accbe67655b3ac57289ea185c245f8f4605973a64697d9db7e83`.
This supersedes the earlier nine-function audit for reproduction with the
current script. Backup before this extension:
`local/ghidra/backups/callback-calendar-before-20261014.tar.gz`.
Fresh source exports: `seattle-message-handler-persisted`,
`seattle-scene-action`, `seattle-scene-timer-leave`, `seattle-date-advance`.
Current full standard-library test suite:124 tests pass; `git diff --check`
passes. The annotation signatures remain unchanged.

## Follow-up: selected merchant whipsaw purchase

The selected original worker observed pre-purchase Aug24/$850/0food, a
merchant whipsaw quote$8, confirmation, removal of that option, and journal
Aug24/$842 with the whipsaw displayed. This is a visible comparison lead;
the state writes below come independently from source/native instructions.

**Observed resource:** TREE2100 at`0x522f6c7`,24664bytes,
SHA-256`eabb9e6ed25f0ff36ebaffb6717c58ae41276ed605657da6d1267a3b36c7e353`.
Normalized option record`+4af0` has condition`(11,109)` and link3. Its child
response`+4c02` uses voice2116 and quotes$8. Confirmation`+4d14` has action
`(220,109,8,0)`, link3; child response`+4e26` uses voice2107. Graph/layout,
initial conditions, original UI action-before-link order and native link
comparisons are documented in [TREE.md](formats/TREE.md).

Merchant constructor `0002:248c` / Ghidra`1008:248c` delegates to dialogue
constructor`0001:0724`, then installs table`0006:66d6`. The relocated table
slot`+10` points to `0002:2884`, which handles opcode220 by passing count1,
amount8 and item109 to `0002:24d0`. Source file offsets are segment2 base
`0xf2c0` plus those offsets; NE segment2 maps to Ghidra`1008`.

`24d0` reads money slots0/1 through `0001:a744`, adds them with **16-bit
wrapping arithmetic**, and compares the sum **signed** against cost8. If it
is less than8, partner4 selects direct `0001:3f9a` OpenScene call arguments
TREE600/kind300 and returns0. The scene creation itself is not emulated by
the state verifier. Success calls `0001:9e40` with the first CONV word17
(CONV2100 identity in TREE.md), which writes raw stateword`+318` if gate`+334`
is0. The meaning of that word remains unknown. It then invokes original
`0001:a184` with−8/slot0, requests optional display-cache927d dirty state,
and maps item109 to `a184(+1,slot6)`. Slot6 is stateword`+306`, the selected
whipsaw inventory word. It returns1. There are no direct date or journal
append calls in this dispatch/purchase path.

Condition`(11,109)` reads that same slot6 at original `0003:5485`, so word306
zero allows the option and nonzero removes it. Twelve original condition
checks in `tree-conditions-recovery-evidence.json` include this rule and
Linda's initial override. This is a selected resource/consumer mapping;
numeric item or condition names alone did not establish it.

`tools/yukonpurchase.py` exposes explicit `WhipsawWords` and
`purchase_selected_whipsaw`, supporting only unowned word306=0, partner4,
CONV17 and action220/109/8/0. It preserves other supplied words, reproduces
the signed wrapping affordability guard, original slot0/bank fallback, gate
suppression, word318 and inventoryword writes. Gate suppression can still
produce success return1 while leaving these state words unchanged: the source
checks affordability before the gated setters. This is not changed into an
invented failure. A refusal returns the selected TREE600 ID without creating
a scene. `whipsaw_option_visible` implements only the selected zero-word test.
General items/opcodes and already-owned purchase dispatch fail explicitly.

**Independent native state proof:** `verify_whipsaw_native.py` executes the
original merchant dispatch2884, purchase24d0, getters, setter9e40 and money
routinea184. It compares112 contexts (cash0/7/8/20/850/32767/32768/65535;
bank0/3/8/20/32767/32768/65535; gate0/1), including full-state sentinel bytes,
return values and refusal-call arguments: zero discrepancies. Original
optional display lookups at `1:a1bd` and `2:2575` returnnull; refusal OpenScene
is an argument-observation boundary. These are explicit exclusions, not a
full original UI execution proof. No arithmetic or inventory behavior is
stubbed. Selected normal result is cash842/bank0/word306=1/rawword318=17.
Matrix and relocated call sites: `whipsaw-recovery-evidence.json`.

```sh
python3 -m unittest tests.test_yukonpurchase
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_whipsaw_native.py \
  original/extracted/windows/YUKON.EXE docs/whipsaw-recovery-evidence.json
```

Eight supported TREE/UI/merchant names/comments were saved through
`AnnotateTree.java` and checked in a fresh Ghidra12.1.4/JDK21 process. The
apply/reopen audits match SHA-256
`37de887dda72f1968ebe2cd41f8cbf0527a7f3ab809cf5a274ea41e94fc32500`.
Backup:`local/ghidra/backups/tree-purchase-before-20261014.tar.gz`; no guessed
parameter signatures were installed. Read-only exports and commands are in
TREE.md. Full browser flow, merchant refusal UI, dates/timers, journal render,
other equipment and general condition coverage remain separate validation.

## Linda opening: selection precedes the seen mark

**Observed source:** dialogue constructor `0001:0724` (Ghidra `1000:0724`)
loads CONV3400, whose first normalized word is4. At `0001:0883` it calls
initial selector `2bc2`, including the TREE3400 `(2,1)` override condition.
Only later, at `0001:0937`, it calls `a2e4` with that CONV word. Setter
`0001:a2e4` reads mutation gate334; with zero gate and index other thanffff,
it writes1 at state`+218+2*index`, then dirties DS52fc objectword54. Linda's
index4 therefore marks stateword220. `9e40` is the separate word318 setter.
Source file offsets are executable base`0x460` plus the listed NE1 offsets.

For a supplied word220=0, the initial selector chooses rootvoice3401 before
the constructor marks220=1. A subsequent open with nonzero220 selects
initial overridevoice3400. A nonzero mutation gate preserves the supplied
word. This establishes ordering, not a fabricated initial save-state value.
`open_linda_dialogue` in `tools/yukontree.py` returns the selected source record
and post-open220 from mandatory raw flag/gate inputs; it excludes allocation,
rendering and other constructor effects.

[Conversation-open native evidence](conversation-open-recovery-evidence.json)
checks constructor source call ordering and CONV/TREE identity, then executes
original selected condition/getter and originala2e4. Eighteen cases cover
220 words0,1,2,32767,32768,65535 × gate0,1,65535 with complete sentinel-state
and dirty-word comparisons: zero mismatches, no operation behavior stubs.
Whole dialogue construction and first/reopen live capture remain separate.

## First Seattle scene visits and the calendar

**Observed resources:** normalized HSPT4000 records1 and2 carry action
words `(1,200)` and dword1000 in the two Downtown exit rectangles. Their strict
hit bounds are preserved by the HSPT consumer. Scene action `0002:0890`
queues opcodes1–3 through manager `0001:4dba`; this is not an immediate generic
date increment. The actual source resource identities and normalized bytes
are in [scene-entry native evidence](scene-entry-recovery-evidence.json).

Normalized SCNE1000 (archive offset85712801,length10) has last word`+8=1`;
SCNE4000 (offset85713021,length10) has`+8=0`. The scene constructor at
`0002:04f0` divides its signed scene ID by1000, calls `0001:a7bc` at0503,
and checks whether the corresponding **visit word** is zero. Gettera7bc reads
state`+2aa+2*index`, so Downtown1000 uses2ac and Wharf4000 uses2b2.
If already nonzero, the constructor skips the first-visit date loop. If zero,
it reads SCNE+8 at0513 and invokes original `0001:a0c2` at054d once per
positive count. At `0002:0592`, `0001:a368` marks that visit word1 unless
mutation gate334 is nonzero. The visit marker itself has no dirty notification.
Source NE2 file offsets are base`0xf2c0` plus the listed offsets; Ghidra maps
NE2 to1008. NE1 getters/setters map to1000/base0x460.

Consequently the selected first Downtown entry advances one original day and
marks2ac=1; a revisit advances none. Wharf requests zero first-visit days.
This source binding explains the independently observed Aug23→Aug24 first
Wharf-to-Downtown transition without making all navigation advance time.
Hidden visit flags were not measured in the live capture; their mapping is
source/native evidence. The scene's other constructor setters, controller
allocation and manager queue processing are excluded from this bounded result.

`enter_selected_seattle_scene` in `tools/yukoncalendar.py` accepts explicit
DateWords, scene1000/4000 and a raw visit word. It composes the established
calendar primitive and visit mark, with no invented initial visit/date state.
The native verifier executes **unchanged constructor block04f0..055b**, actual
gettera7bc/datea0c2 calls and markera368. Ninety-six comparisons cover both
scenes × six visit words × four date/counter boundary contexts × gate0/1;
full state bytes and dirty54 match with no behavior stubs. This proves the
selected caller branch as well as the primitive; it does not execute an entire
Windows scene transition.

### Separate animation countdown setup

`0002:1036` sets global DS1188 to its requested signed positive count, coercing
nonpositive values to1. If scene animation pointer+18 is null, it constructs an
18-byte object, sets scene+1e from the timer helper with `120/count+30`
(`+5` only for sceneID4a38), and sets scene+1c through that helper with2.
Constructor057c calls1036 only when existing DS1188 is signedpositive; scene
action140 calls it with nonzero actionword2. The previously recovered timer
0740 decrements this countdown while calling datea0c2. These animation/timer
allocations and OS services have **not** been native-emulated here. They are
separate from the immediate SCNE+8 first-visit loop and must not replace it or
be attached to every navigation action.

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_conversation_open_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/conversation-open-recovery-evidence.json
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_scene_entry_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/scene-entry-recovery-evidence.json
python3 -m unittest tests.test_yukontree tests.test_yukoncalendar
```

The standard-library suite now passes154 tests. `AnnotateTree.java` adds four
source-grounded function names/comments for the seen marker, visit getter,
visit marker and countdown setup, retaining the existing eight annotations.
Backup:`local/ghidra/backups/scene-conversation-before-20261014.tar.gz`.
Read-only `DecompileSmoke.java` exports at1000:a2e4/a7bc/a368/a314 and1008:1036
are under `local/ghidra/`. The bounded proofs use Python3.14.5/Unicorn2.1.4;
no source files or original saves are modified.

Fresh Ghidra JVM verifies all12 names/comments: identical25-record apply/reopen
audits, SHA-256 `75342e3d59b44127259fb153b207edc79d447d00074f9da9ffa8a9f3ddd210f9`. No active project process remains.

## Original raw reset defaults

**Observed source:** cash350 is written by the instruction starting
`0001:9983` (file0x9de3;9986 is inside its encoding). Its encompassing routine
is `0001:9900..9bb8`, Ghidra1000:9900, source filebase0x460. It explicitly
sets these raw words; they are not inferred from visible labels:

| State offset | Reset value | Established selected meaning |
| --- | --- | --- |
| 028 / 02a | 23 / 8 | Day / month |
| 30e / 310 | 1 / 1 | Elapsed word / phase word |
| 312 | ffff | Original no-partner sentinel |
| 220 | 0 | Linda conversation-seen word |
| 2ac / 2b2 | 0 / 0 | Downtown / Wharf visit words |
| 2fa / 2fc | 350 / 0 | Cash / bank |
| 2fe / 300 / 302 / 304 / 306 / 308 / 30a | all0 | Original inventory slots2–8; only selected whipsaw306 semantics established here |
| 318 / 334 / 344 | all0 | Selected action mark / mutation gate / acceptance word |

The reset zeroes61 conversation words from218,40 visit words from2aa,
additional source arrays and many other individual fields. It clears only the
first bytes of the two name buffers at0/14. **It does not memset the entire
state.** Bytes not written remain supplied prior bytes, including locationword34,
name tails, holes and any bytes after386. Maximum direct write is word384;
therefore the supplied state buffer must contain at least0x386 bytes. Scene
entry and name/journal editing are separate operations. Do not manufacture
zero defaults for the preserved bytes or treat a reset as an entire fresh UI
session. `tools/yukoninitial.py` and `web/rules/initial.mjs` preserve those bytes.

The reset calls original `0006:2a28`, Ghidra1028:2a28/file0x479e8. It executes
32-bit multiplication through6:2c48 and computes
`next_seed=(seed*214013+2531011) mod 2^32`, stores it at DS483e/4840, then
returns `(next_seed>>16)&7fff`. Reset uses output modulo3 to set314/316 to
7/10,8/11 or9/12; the meanings of these two words remain unknown. The model's
`original_random_step`/`originalRandomStep` requires an explicit seed, and reset
requires the explicit random output. **OS/startup seeding is unrecovered; no
fixed seed is installed as an original-game default.**

Three observed callers are `0001:9394` in constructor929e, `0001:970e` in
9698, and reset wrapper98ea at98f2. Wrapper98ea calls9900 then returns the same
far pointer. Constructor929e clears global DS1188 at9368, calls reset9900 at
9394, then clears journal text's first byte through DS5304 object's far+0e at
939f and sets that object's word+a to1 at93a7. These constructor/journal/global
bindings are source observations; the complete constructor and its helper8aec
have not been native-executed here. Caller9698 can overwrite the reset during
loading, so a reset proof does not establish loaded-save state.

[Initial-state native evidence](initial-state-recovery-evidence.json) executes
unchanged original9900, original RNG2a28/multiply2c48 and memset291e. Only far
selectors are relocated; **no random, memory-fill, allocation or state behavior
is stubbed**. Thirty-six comparisons use12 controlled32-bit boundary seeds ×
zero/55/ramp prior buffers, comparing all0x400 supplied state bytes and the
updated seed: zero mismatches. The sentinel sample, selected words, every
full-buffer hash and relocated call sites are retained. Both Python and Node
models match these measured original full-buffer hashes. The selected starting
calendar/partner/flags/inventory words are therefore established while excluded
whole-session and seed dependencies remain explicit.

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_initial_native.py \
  original/extracted/windows/YUKON.EXE docs/initial-state-recovery-evidence.json
python3 -m unittest tests.test_yukoninitial
node tests/test_browser_initial.mjs
```

Python3.14.5, pinned Unicorn2.1.4, Node26.0.0. `ProbeFreshState.java` exports
the containing initializer and its three source call references. Dependency
probes use `DecompileSmoke.java` at1028:2a28/2c48/291e and1000:929e/9698/98ea.
`AnnotateInitialState.java` persists three function names/comments without
guessed signatures. Backup:`local/ghidra/backups/initial-state-before-20261014.tar.gz`.

Fresh Ghidra JVM verified all3 initial-state names/comments: identical7-record
apply/reopen audits, SHA-256
`70ec8ac321c7348b78839f574e459a48c137cba0dbf56ac183bff1393f98ea1f`.
Standard-library suite157 passes; Node initial module matches all36 original
full-buffer/RNG cases.

A separate source check prevents conflating tracking words with location:
Seattle constructor0093's `9f14(200)` writesstate332, and00a4's
`a4ce(sceneID)` writesstate330, both gated334. They do not assign locationword34.
Reset9900 preserves34 while clearing36/38; the reset alone excludes scene location initialization; the selected constructor
binding is recovered in the follow-up below. These two constructors' tracking setters were inspected
in disassembly but are not included in the36 reset native cases.


## Actual Seattle location tuples and journal support

The earlier `(200,0,0)` journal input was an explicit bounded fixture, not a
measurement of the fresh game's hidden location words. **Observed source/native
follow-up:** Seattle constructor `0002:00e6..0214` sets `(200,0,sceneID)` for
selected sceneIDs1000,2000,3000,4000. At020f it calls `0001:9ffa` (Ghidra1000:9ffa,
sourcefile0xa45a), which copies three supplied words into34/36/38 and dirties
DS52fc object's54, unless gate334 is nonzero. Reset9900's preserved34 is thus
assigned by scene entry, independently of the330/332 tracking setters.

[Scene-location evidence](scene-location-recovery-evidence.json) executes the
unchanged constructor switch and actual9ffa setter for all four selected scenes
× gate0/1, with complete sentinel-state comparison: eight cases, zero mismatches.
For each ungated tuple it also executes original journal place helpercff8,
which appends original Data13:0fa2 bytes `Seattle. `, without state changes.
Only far selectors are relocated; no constructor-switch, setter, heading or
string behavior is stubbed. Resource allocation and the rest of the constructor
are outside the bounded execution.

**Source disassembly guard:** cff8 checks firstword200 at `0001:d1eb`, but still
uses SECOND word as a32-byte place-table index atd1f2/d1f5. Thirdword is not
used on this selected branch. Consequently the supported formatter bound is
firstword200, secondword0, thirdword any explicit unsigned16-bit word. Other
regions or second indices continue to fail; allowing arbitrary second words
would be a material error. Both `tools/yukonjournal.py` and `web/rules/journal.mjs`
now implement that bound, supporting actual `(200,0,3000/4000)` without replacing
the scene ID with an invented0. The Python historical default remains the
original fixture, not a fresh-state initializer; JS requires the explicit tuple.

[Journal metadata](journal-recovery-evidence.json) preserves the original576-case
fixture matrix hash unchanged and adds **48 full native formatter comparisons**:
thirdword0,1,1000,3000,4000,32767,32768,65535 × three date/phase contexts ×
empty/nonempty prior journal. All entries and state-preservation checks match.
New matrix SHA-256 `4fbc32f05b721b8daf64ba4af4eb9e5bab5dc1bd0a3e016a9c555cd62dfed361`.
Node checks match all48 recorded native output hashes in addition to576 historical
cases and three queue cases; standard-library suite158 passes.
Live comparison still establishes only visible journal/date/money, with hidden
location words explicitly excluded; the tuple mapping here is separate source/
native evidence, not a retroactive live-memory observation.

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_scene_location_native.py \
  original/extracted/windows/YUKON.EXE docs/scene-location-recovery-evidence.json
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_journal_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/journal-recovery-evidence.json
python3 -m unittest tests.test_yukonjournal
node tests/test_browser_journal.mjs generated/browser-proof-20261013/journal.json
```

The Node fixture is reproducible with `prepare_journal_assets.py` into a fresh
ignored JSON path; it carries source vocabulary and CSTR505 provenance. Updated
`AnnotateJournal.java` persists the corrected place-index/third-word comment;
`AnnotateInitialState.java` additionally names9ffa. The earlier full reset/RNG
proof remains36cases and no fixed startup seed/default is introduced.

Fresh JVM persistence checks pass for all4 initial/location and12 journal/scene
names/comments. Apply/reopen audits are identical:

- initial-location: 9 records, SHA-256 `e118433b152eb78273eaf7bd1f884c6a31431aef3ff7ef7a3646c71a23fc2a8f`.
- journal-location: 25 records, SHA-256 `99ab284b800ba7670f23627dad6640dc3cff6e65babab9f32737f311450f45d1`.

The same original first-visit branch has additionally been checked for SCNE2000
(offset85712921) andSCNE3000 (offset85713011): both word+8 are0, and only1000
requests1 first-visit day among the four selected Seattle scenes. Calendar
models now explicitly support1000/2000/3000/4000; other sceneIDs still fail.
`scene-entry-recovery-evidence.json` expands the original caller/state matrix
to192 comparisons, zero mismatches, retaining actual resources/hashes. Node
checks match all192 recorded full-state hashes; the earlier96-case checkpoint
covered only1000/4000. This remains a bounded constructor date/visit effect,
not a complete scene transition, timer, or general navigation implementation.
