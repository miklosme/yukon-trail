# Countdown and voyage investigation

Current supported implementation is **only the bounded rule blocks below**,
not the complete animation, timer callback or voyage. Source EXE SHA-256:
`9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`.
NE2 maps to Ghidra1008; NE4 maps to1018. Original media remain unchanged.

## Proven rule blocks

Saved original NE2:0740 disassembly shows: if scene animationfar+18 is null,
the routine returns. Otherwise it calls animation rendering; signed global
DS1188>0 then calls rendering/animation advance, calls date NE1:a0c2 at07a4,
decrements DS1188 at07a9 and returns. Reaching countdownzero does not queue
travel in that same positive-count invocation. A subsequent invocation takes
the exhausted-count branch and cancels timers, removes/destroys/frees the
animation, clears its pointer and selects a queue by sceneID.

`advance_countdown_day_block`/`advanceCountdownDayBlock` implement original
NE2:079f..07ae after the animation updates, using the independently recovered
calendar. Inputs are full explicit raw state bytes and a signed-positive
original countdown1..32767. Date writes are suppressed by gate334; countdown
decrement is not suppressed. Unsupported branch inputs fail explicitly.

`finish_wharf_countdown_block`/`finishWharfCountdownBlock` implement original
NE2:0817..088c after animation/timer cleanup. Caller prerequisites are explicit:
sceneID4000, old animationpointer stillnonnull, timerwords+1c/+1e alreadyffff,
signed countdown<=0. Original instructions clear scene+18, set state33a=0
through gated NE1:a530 and queue manager `(1,400,31000,0)` through NE1:4dba;
manager+2=1 and its8byte action+4 is copied. No date increment occurs here.
Neither function invents a timer, animation pointer, timer IDs, default date
or elapsed-time assumption. The prerequisites are not new game eligibility
rules: they describe where the verified original execution blocks begin.

`countdown-block-recovery-evidence.json` records48 original day/decrement
contexts (four date/counter/phase cases including month/year ends, four positive
countdown values, gate0/1/ffff) and9 original post-cleanup queue contexts
(count0/8000/ffff, gate0/1/ffff). All full state/scene/manager bytes match.
The verifier executes unchanged blocks and actual date/setter/copy/queue
functions, with explicit synthetic caller frames and far selectors relocated;
**no behavior stubs**. Animation calls before079f, and timer/animation cleanup
before0817, are outside these execution bounds and are not claimed validated.
Node compares the same original oracle hashes. Five Python tests additionally
check original month-end behavior, gated decrement, no early queue and explicit
cleanup prerequisites. Models are in `tools/yukoncountdown.py` and
`web/rules/countdown.mjs`; no browser integration is included.

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_countdown_native.py \
  original/extracted/windows/YUKON.EXE docs/countdown-block-recovery-evidence.json
/opt/homebrew/bin/node tests/countdown-oracle.mjs
python3 -m unittest tests.test_yukoncountdown -v
```

Tool versions: Python3.14.5, Unicorn2.1.4, Node26.0.0. Ghidra12.1.4/JDK21
saved source export `local/ghidra/seattle-scene-timer-leave.asm.txt` at1008:0740.
See `TICKETS.md` for the original request leading to countdown or direct travel.

## Voyage entry lead, still under recovery

Archive31000 is not a normal SCNE/HSPT/SCRP/TREE/CONV scene. There is one
SMAP31000 resource at archive0x51bf749,272bytes, SHA-256
`6d21c1f73a01b1f6a13cb31dd55016fcbf32e1c30004c9b116e29b3f964369fa`.
Its registered postread pattern is(-7,0), word swapping. The first normalized
word is45, followed by45six-byte records; field semantics require consumers.
Raw factory NE1:427a explicitly compares31000, category400, and42a3 calls
NE4:2b8c. NE4:2b97's source selector relocation at2b9a targets segment4, so its
base constructor call364a is **NE4:364a**, notNE1. The bounded constructor
state writes and original waypoint3482/arrival41e0 now have independent native
models/oracles in [VOYAGE.md](VOYAGE.md). Full constructor/render/journal,
schedule/check-partner, full daily callback composition, cutscenes and voyage
dates remain unimplemented and must not be replaced by an inferred journey.
Selected sea-day2a8e rules are now recovered separately in [SEA-DAY.md](SEA-DAY.md).

The independent original worker's Al-Ki reference records boarding August24,
map August28, storm August28 and Skagway arrival September10. These observed
dates are comparison targets, not defaults or unexplained date jumps inserted
into the recovered countdown blocks.

## Recovered timer service

Original NE1:4e94 constructor clears exactly five4-byte far pointers; it leaves
any extra caller bytes unchanged. Original4f20 scans slots0..4 for the first
null pointer; fulltable returnsffff without allocating or reading the clock.
It allocates8bytes through NE6:1ebe. Allocationfailure leaves the slotnull and
returns the selected slot index, notffff. Success sets recordbyte0=1, copies
the raw periodword at+2 and sets the32-bit deadline+4 to
`(TIMEGETTIME() >> 4) + signed16(period)`, modulo2^32. Recordbyte1 is untouched
allocator padding, not an invented zero or flag. Allocation and clock values
are explicit platform inputs in the model.

Original TIMEGETTIME callsites1:4f81,507c,50f9 share the raw NE imported-far
fixup chain1:4f82→507d→50fa→ffff, import module6/MMSYSTEM ordinal607. The
Ghidra relocated symbol is TIMEGETTIME. This proof retains its originalu32
clock value and logical shift>>4; it does not assign a browser polling cadence.
For selected Wharf4000, original1036 normalizes signed requestedcount<=0 to1
and computes period `120/count+30`. The other animation timer usesperiod2.
Counts7/14 therefore request47/38clockquanta, respectively. Ten native tests
execute normalization103a..1045 and exact periodblock10c4..10e6. Special
scene19000's+5 branch is not exposed by this selected helper.

Original1:5076 snapshots the shifted clock once, loops slots0..4 in order,
and forwards message0466 with timerID and zero data for each nonnull record
whose unsigneddeadline<=snapshot and activebyte is nonzero. Each slot fires
at most once per poll. After forwarding, it rereads the current tablepointer;
if stillnonnull, it reads TIMEGETTIME again and resets deadline from **that**
fresh clock plus the current signed period. It does not advance the old
deadline repeatedly to catch up. Callback cancellation skips rescheduling;
callback disabling leaves a pointer and still resets its deadline.

Original4fca clears/frees a timer pointer. Its signed guard accepts0..5,
although constructor/register/poll only coverfive slots0..4. Natural registered
IDs are0..4/ffff. The one-past-constructor index5 path is explicitly excluded
from the model rather than accessing adjacent unknown memory; other negative
signed IDs and IDs>5 preserve the table. This observed guard discrepancy is
not interpreted as a sixth supported timer.

`tools/yukontimers.py` and `web/rules/timers.mjs` provide these operations with
explicit byte buffers, allocator result/farpointer/record, clock values and
forwarded-event callback. Polling callbacks can mutate the copied table and
records. These models neither run nor assume a game scene callback. The
clock/allocator services and event boundary are the only controlled consumers
in `verify_timers_native.py`; original timer code and memory writes execute.
`timer-recovery-evidence.json` records:

- 3 original constructor patterns, preserving bytes beyond20.
- 3,456 registration cases: all32 slot-occupancy masks, nine periodwords,
 six clock boundary values, allocation success/failure.
- 288 cancellations: all32 masks and nine supported raw IDs.
- 180 polling cases: five clocks, four active-byte values, deadlinebefore/
 at/after snapshot and keep/remove/disable callbacks. Native event arguments,
 clock-read counts, tables and record bytes match.
- 10 selected count normalization/period calculations.

Node matches every original timer oracle output; six Python tests cover source
extent, padding/failure semantics, no catchup, fresh-clock scheduling and callback
cancellation. Commands:

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_timers_native.py \
  original/extracted/windows/YUKON.EXE docs/timer-recovery-evidence.json
/opt/homebrew/bin/node tests/timers-oracle.mjs
python3 -m unittest tests.test_yukontimers -v
```

## Supported boundary and remaining work

Original animation draw4:a0f4 reads the date through1:a68e and draws month/day
text through GDI wrappers;4:a396 reads rawphase310 through1:a850, updates image
frames and child clock fields;4:a424/a0a2 remove/free its image objects. Source
exports are `countdown-animation-draw/advance/remove/destroy` underlocal/ghidra.
Those rendering/virtual callbacks are not included in the57 bounded rule-block
comparisons. Timer creation/cancellation/registration are recovered above, but
animation construction9e8c, full active-scene message routing and complete0740
callback execution/render fidelity are still separate proof obligations.
The source predicates requiring actual active scene/timerID and nonnull
animation must be composed by the calling engine, not inferred from a request
alone. This handoff supplies no new UI or automatic voyage/date default.

## Analysis-project persistence

`AnnotateVoyageCountdown.java` saved seventeen observed function names/comments
and two fixed-width resource structures (`OriginalTimerRecord8` and
`SMAP_ObservedWaypoint6`) in the original NE analysis project. Existing
NE2:0740/1036 annotations were retained. A separate read-only process reopened
the project and verified all44 source/name/comment/type/field audit records;
applied and reopened files are byte-identical, SHA-256
`423e1b0a314b9de966d558411c609cac0d7d4ce35899bca9ece70afca58a5740`.
No guessed function signatures were installed. Ghidra12.1.4 and JDK21 were used.
The ignored pre-change backup is
`local/ghidra/backups/voyage-countdown-before-20261014.tar.gz`. Reproduce after
obtaining exclusive project access:

```sh
tools/ghidra/headless.sh "$PWD/local/ghidra" YukonTrail -process YUKON.EXE \
  -noanalysis -scriptPath "$PWD/tools/ghidra" \
  -postScript AnnotateVoyageCountdown.java apply local/ghidra/voyage-countdown-applied.tsv
tools/ghidra/headless.sh "$PWD/local/ghidra" YukonTrail -process YUKON.EXE \
  -noanalysis -readOnly -scriptPath "$PWD/tools/ghidra" \
  -postScript AnnotateVoyageCountdown.java verify local/ghidra/voyage-countdown-reopened.tsv \
  -postScript ProbeVoyage.java local/ghidra/voyage-bindings.asm.txt
```
