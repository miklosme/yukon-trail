# Selected sea-day and event rules

The selected sea context now has recovered Python and JavaScript operations for
original NE2:2a8e, weather selector3188, sea-event updater32fa, and sea-message
selection2c8c. This covers explicit date, counters, weather, food, RNG and pending
message/status effects. It does not establish a full voyage or a fresh world
object. Caller timing, resource ownership, notification/journal and cutscene
consumers remain separate obligations.

Source EXE SHA-256:
`9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`.
Archive SHA-256:
`438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`.
NE1/2/6 map to Ghidra1000/1008/1028, file bases0x460/0xf2c0/0x44fc0;
data13 maps1060, filebase0x4f420. These remain segmented source addresses.
Source exports are `local/ghidra/seaday-{consumers,event,weather,journal,
state-getters,cstr-consumers,seenflags}`. The decompiler's apparent unrestricted
integer multiplication in3188/32fa was checked against original IMUL/CWD/IDIV
instructions and callers before implementation.

## Explicit inputs and selected domains

`tools/yukonseaday.py` and `web/rules/seaday.mjs` expose
`sea_event_update`/`seaEventUpdate`, `sea_weather_update`/`seaWeatherUpdate`,
`advance_sea_day_before_journal`/`advanceSeaDayBeforeJournal`,
`sea_message_update`/`seaMessageUpdate`, and composed
`advance_sea_day`/`advanceSeaDay`. They require actual state/world/context/text
bytes and an explicit original u32 RNG seed. They neither allocate a zeroed
world object nor choose a seed, timer cadence, date or starting weather.

The context is the far tuple addressed by parameter2, bound in the caller to
scene+22; constructor2b8c sets its first word0 for sea travel. The message model
supports ships1/2/3, context+4 values0/1/2, world+28 markers0/1 and world+2a
markers0..6, all produced by the selected consumers. Actual SMAP31000's row+2
values are exactly0/1/2 (see [VOYAGE.md](VOYAGE.md)); the message model rejects
other domains instead of reading outside established flag/string extents.
The lower-level event routine independently supports raw u16 boundaries shown
in its native matrix. Other context categories1/2 in2a8e are excluded.

## Day operation NE2:2a8e

For sea context firstword0, original2a8e clears world words+2/+6/+8/+a/+c.
NE1:a098 decrements state31e with16-bit wrap, then clamps a negative signed
result to0; gate334 suppresses that state write. Gettera734 returns31e. If the
signed result is<=0,2a8e clears world0/+22 and invokes3188. World writes and RNG
are not suppressed merely because334 is nonzero.

Original date1:a0c2 then advances one fixed-calendar day, obeying334, including
elapsed30e and phase310 mutations established independently in
[SEATTLE-RULES.md](SEATTLE-RULES.md). If state31a is exactly0, it calls32fa.
Then1:9ec6 decrements31a with the same wrapped/signed-clamped/gated semantics;
gettera67e returns31a. A signed result<=0 clears world+0e. It calls2c8c to
select the pending sea message/status and clear processed markers.

The before-journal operation stops immediately before original2b68's2c8c
call. The composed operation includes the message effects described below,
with explicit CSTR2000 data. No automatic daily12-pound food consumption occurs
in this selected context0 branch; such consumption in context1/2 is outside
this operation. Food can change through the original weather/event loss paths.

## Weather selector NE2:3188

For selected sea context0,3188 clears world+28 and draws original RNG6:2a28.
Its first output%100 selects world0: below55→0,55..74→1,75..99→2. Values>=55
increment state32e through1:a942, **without334 gating**. For world0=2 it consumes
a second RNG output and attempts food loss when ship320!=3 and output%100>=80.
Otherwise it clears world+6/+8. This sea storm sets world+28=1.

Food loss consumes a third RNG output; percentage is output%15+1. It gets
inventoryslot2/state2fe through1:a744 and multiplies by the percentage. Original
IMUL at3188's31ff then CWD at3204 sign-extends the **low wrapped16-bit product**
before signed division by100. Consequently high/outlier food words do not
follow an unbounded percentage formula. The loss word goes to world+8;
original1:a184 subtracts it from slot2, wraps16 bits and clamps a negative
signed result to0, obeying334. No bank/cash fallback or display-cache lookup
occurs for slot2. Native boundary matrices preserve this behavior.

Finally3188 writes current world0 to state31c via1:a050, draws another RNG
output, and writes duration(output%4+3) to31e viaa074. Both setters obey334.
This duration is a rule word, not an inferred browser delay. The non-sea month/
freeze branch and its31a/342 writes are excluded from the selected weather API.

## Sea-event updater NE2:32fa

32fa reads ship320, then compares world+18 as signed. If<=2 it only increments
that counter, wrapping16 bits, and consumes no RNG. If>2 and context+4=0, it
clears world+2/+2a, **skips counter reset**, then increments the existing counter.
This distinction was exposed by the original full-buffer oracle and fixed in
the model before handoff.

For signed counter>2 and context+4 nonzero, it draws RNG and computes
`output%100 - 3*(ship-1)` with16-bit wrap and signed comparison. Below60 clears
world+2/+2a. Otherwise world+2 becomes1 when context+4==1,2 otherwise;
world+2a becomes `2*(ship-1)+world+2`, wrapped16 bits; world+4 becomes1. It then
consumes a second RNG output and uses the same ship!=3, output%100>=80 food-loss
path above, or clears world+6/+8. A selected event increments32e ungated.
After either nonzero-context outcome it resets world+18 to0; the common final
increment makes it1. These fields are raw source words; names such as rocks/
iceberg are supported by the selected CSTR text, not assumed for other values.

## Sea-message consumer NE2:2c8c

The original sea branch reads pending world+2a first. If nonzero, it writes
world+32=marker+3 and reads the corresponding original event-seen word through
NE1:9cce, state offset `0x19e + 2*index`. If unseen it selects CSTR2000 index
`3*context+4 + ship-1`, copies the text to the far buffer at world+10, and sets
status+1c=marker+33. If that event was seen, it falls back to pending world+28.
If+28 is nonzero it writes+32=marker and reads that seen flag; if unseen it
selects indexship-1 and sets status+1c=marker+30. If neither is selected, status
is0 and existing text is preserved. Even a seen candidate can update world+32.
This consumer **reads, never sets**, event-seen flags.

It copies the selected string through original NE6:1f22 (`strcpy`, not append),
including its terminator; bytes beyond that terminator are preserved. Selection
uses original NE2:2040 and strlen6:1f88. It then clears world+2c/+28/+2a/+2e/+30.
Subsequent partner notification, seen marking and journal effects are not
executed by the model.

Actual CSTR2000 is at archive0xbdf7cb (decimal12449739),605bytes, raw SHA-256
`c661ae6e55225c4f9245d092c6c7127f75a44a262cde8aa3edb72609c6d4d3a8`.
Registered postread swaps its countword only. It contains9 byte strings: three
ship variants each for storm, rocks and iceberg. `read_sea_event_strings`/
`readSeaEventStrings` preserve the exact bytes and require the source count and
terminated extent. Resource metadata, normalized hash and all nine strings are
retained in `seamessage-recovery-evidence.json`.

Original CSTR constructor2:1f98 allocates18bytes, calls resourceclass1:e9d8,
and GLOBALLOCKs its handle into instance+4. Destructor2:1ff8 GLOBALUNLOCKs,
destroys that class1:ea70 and frees it, then clears+4. Native message/combined
checks stop at these ownership call boundaries, supply an explicit locked
instance with actual normalized source bytes, and resume the original game
blocks. They do **not** claim execution of Windows handle/cache lifetime or
substitute selection/copy/status rules. Resource ownership remains an explicit
platform proof boundary.

## Independent verification and commands

Python3.14.5, Unicorn2.1.4 and Node26.0.0 were used. Original instructions and
called game-rule consumers run unchanged; far selectors are relocated. Reports
retain source identities, full-buffer output hashes, RNG seeds and branch inputs:

- `seaday-event-recovery-evidence.json`:10,500 u16/signed boundary cases plus
 1,944 targeted RNG cases, including every1..15% loss and exact first/second
 chance thresholds; zero mismatches.
- `seaweather-recovery-evidence.json`:2,184 original context0 cases, including
 exact54/55/74/75 and79/80 thresholds and every loss percentage; zero mismatches.
- `seaday-block-recovery-evidence.json`:1,440 date/counter/gate cases plus648
 targeted contexts, stopping before2c8c; zero mismatches.
- `seamessage-recovery-evidence.json`:1,134 message/seen/fallback cases, exact
 state/world/text buffers across the explicit CSTR ownership boundary.
- `seaday-combined-recovery-evidence.json`:864 date/counter/gate contexts plus
 432 source ship/context/seen cases for original2a8e with all selected consumers.

All five Node oracle checks match the same native state/world/text/RNG hashes.
Ten Python tests cover original counter-reset differences, signed wrap, gated
food versus ungated32e, low-word food product, calm duration, month boundary,
seen-event fallback and unsupported contexts. Source strings are never treated
as generated prose. Reproduce with exclusive Ghidra access only for probes;
native/Node checks do not open the original UI or a browser:

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_seaday_native.py original/extracted/windows/YUKON.EXE docs/seaday-event-recovery-evidence.json
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_seaweather_native.py original/extracted/windows/YUKON.EXE docs/seaweather-recovery-evidence.json
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_seaday_block_native.py original/extracted/windows/YUKON.EXE docs/seaday-block-recovery-evidence.json
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_seamessage_native.py original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE docs/seamessage-recovery-evidence.json
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_seaday_combined_native.py original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE docs/seaday-combined-recovery-evidence.json
/opt/homebrew/bin/node tests/seaday-oracle.mjs
/opt/homebrew/bin/node tests/seaweather-oracle.mjs
/opt/homebrew/bin/node tests/seaday-block-oracle.mjs
/opt/homebrew/bin/node tests/seamessage-oracle.mjs
/opt/homebrew/bin/node tests/seaday-combined-oracle.mjs
python3 -m unittest tests.test_yukonseaday -v
```

## Remaining caller and live-comparison boundaries

NE4:3224/3f6a timer routing, fifth-tick cadence, waypoint/rate changes, world
construction and full visual/calendar animation composition remain separate
from this rule operation. NE2:2fea partner/dialogue opening, event-seen marking
and journal notification must be recovered next; the pending message text is
not itself a journal append. Cutscenes31101/31102/31103 and their return paths
remain unimplemented. The live Al-Ki Aug24/Aug28/Sep10 dates are still comparison
targets, not hard-coded jumps. No end-to-end voyage, audio, save or browser claim
is made from these native rule comparisons.
