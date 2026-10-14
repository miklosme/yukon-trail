# Selected sea-map progression recovery

This implements the original waypoint routine and bounded constructor writes,
not a completed voyage. `voyage-waypoint-recovery-evidence.json` retains every
actual SMAP row, source hashes/offsets, source speed words and native input/output
cases. Source EXE SHA-256:
`9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`;
archive SHA-256:
`438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`.
NE1/2/4/6 map to Ghidra1000/1008/1018/1028. No flat executable address is
substituted for these segmented source addresses.

## Entry and data

Category400/resource31000 factory NE1:427a/42a3 selects NE4:2b8c, allocating
0xa6bytes. There are no SCNE/HSPT/SCRP/TREE/CONV31000 resources. Constructor
2b8c calls base NE4:364a, then installs vtable NE6:8afe. Its slot4 is message
handler NE4:3224; slot10 is inherited3aa0; slot20 is3126. The first base table
is NE6:8b54. Pointer words and source callees are checked in
`local/ghidra/voyage-bindings.asm.txt`.

Base constructor36a2..36e0 calls NE1:9f14 with400 (state332), a4ce with31000
(state330), then reads336 viaa8d0 into scene+88 and338 viaa8e0 into scene+8c.
Both setters obey gate334; the reads/local scene writes still occur when gated.
`initialize_map_state_block`/`initializeMapStateBlock` implement only this block.
Thirty-two original full-state/scene comparisons cover saved336/338 boundary
values and gate0/1. These writes do not advance a date or initialize336/338.
Their initial zero values are independently established by original reset9900.

Constructor2b8c loads SMAP31000 at archive0x51bf749,272bytes, SHA-256
`6d21c1f73a01b1f6a13cb31dd55016fcbf32e1c30004c9b116e29b3f964369fa`.
Original registered postread pattern(-7,0) swaps all words. The normalized
firstword45 is followed by45six-byte records. Each record has three16-bit
words. The waypoint consumer below reads word+4 as an event; firstword and
word+2 are retained raw here (renderer/direction consumers remain separate).
`read_sea_map`/`readSeaMap` accepts this count/extent and only observed event
values0,1,2,31101,31102,31103; truncation, extra data or unknown events fail.

After locking the SMAP buffer, constructor stores its count at+94 and first
rowpointer at+98. It starts a timer with period35 through NE1:4f20, storing
ID+8e. Constructor sets a location tuple at scene+2a `(400,0,scene+88)` and
calls original State_SetLocationTuple9ffa. If+88=0 it calls journalc474 with
event1/status0 at2c6c, then changes an image slot. These additional constructor
effects and resource/rendering allocations are source-traced, **not included**
in the bounded constructor model. No direct calendar call occurs in2b8c/364a.

## Original waypoint operation

NE4:3482 adds scene speedword+96 to partialword+8c with16-bit wrap. It compares
the wrapped result as signed: if less than25 it saves current progress without
consuming a row. Otherwise it subtracts25 **once**, reads the current row+4
event from SMAPbase+98 indexed by scene+88*6, and handles that event:

| Event | Original effects before saving progress |
| --- | --- |
|0|scene+80=0,+7a=0; index+88 increments1|
|1|+7a=1; if original inventoryslot8/state30a==11, queues `(2,300,26000,0)`; index increments|
|31101/31102/31103|+80=1,+7a=1; opens that resource with category1700; index increments|
|31102 additionally|if global soundmodeDS00b0!=2, invokes audio at scene+ a2 before opening the cutscene|
|2|index+88=0,partial+8c=0,+7a=1,+7c=1; queues `(1,200,destination,0)`|

For event2, destination is state322 if5000/Dyea or9000/Skagway. Only another
value draws original RNG6:2a28 once: output%2=0 selects5000, otherwise9000.
Original NE4:41e0 builds the arrival queue; it does not construct the new scene.
No destination correction/default is inserted. Source meaning of inventory
slot8==11 and event1's26000 conversation remains unknown here.

Finally3482 writes current local index/partial to state336/338 through NE1:a4e8/
a50c, both gated334 with dirty notification. Those words record intermediate
progress even when the threshold is not reached. One call consumes at most one
row even if the remainder is still>=25. It does not change date, cash, food,
ship or destination. OpenScene and audio calls are observed consumer boundaries:
their cutscene/dialogue/audio effects are not silently executed by the model.

Models: `tools/yukonvoyage.py`, `web/rules/voyage.mjs`. Inputs require explicit
state, scene and manager bytes, source rows, RNG seed and soundmode. The scene
index must be within0..44; corrupt/out-of-range reads are excluded rather than
emulating arbitrary memory. Speed is an explicit original scene word, not a
new difficulty setting. Native data segment13:14cc contains nine speed words
`18,15,9,15,10,6,9,7,4`; their selection depends on the daily consumer below.
No browser, animation renderer, image overlay or audio playback is supplied.

## Native comparison

`verify_voyage_native.py` executes unchanged3482, arrival41e0, getters/setters,
queue/copy and RNG. Far selectors are relocated. OpenScene arguments and the
31102 audio invocation are recorded at their boundaries; no progression,
condition, queue or RNG behavior is stubbed. Full0x400-byte state,0xa6-byte
scene,128-byte manager, final seed and requested consumers match in:

- 5,940 cases: all45 source rows × six partial boundary words × eleven rates
 (all distinct original speed words plus0/7fff/8000/ffff) × gate0/1.
- 108 targeted event1/2/31102 cases: destination0/5000/9000, inventory0/11,
 soundmode0/2, three seeds.
- 32 constructor state-block cases described above.

Node compares the same original hashes and consumer outputs. Four Python tests
check actual source-row parsing/bounds and important original one-row/arrival
behaviors. Commands (Python3.14.5, Unicorn2.1.4, Node26.0.0):

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_voyage_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/voyage-waypoint-recovery-evidence.json
/opt/homebrew/bin/node tests/voyage-oracle.mjs
python3 -m unittest tests.test_yukonvoyage -v
```

## Daily progression and unresolved consumers

Actual3224 handles0466 only for timerID scene+8e. It calls3482 first. If signed
scene+7e<1, it increments local tickcounter+8a. At exactly5 it sets scene+26
from the **current** SMAP row+2 and calls generic map NE4:3f6a with scene+7a.
That routine obtains the date. If+7a is nonzero and worldobjectDS5300+0e!=1,
it advances one day directly; otherwise it calls world/day NE2:2a8e, which
resets world fields, decrements state counters, advances a day, updates events/
inventory/weather and selects a pending message. The selected sea context0
operation and its exact CSTR2000 consumer are now recovered in
[SEA-DAY.md](SEA-DAY.md), with explicit resource-ownership boundaries. It later updates
the date animation and resets tickcounter+8a. These operations are not modeled
by the waypoint routine; neither five ticks nor a waypoint is assigned a guessed
calendar date in the port.

The message handler subsequently chooses rate-table offset0/3/6 according to
world fields and current row+2, and chooses the final rate using world words;
other status flags can set ratezero. Cutscene callbacks046a/046b alter pause
flags and overlays. Exact daily/world inputs and the creation/return of
31101/31102/31103/category1700 remain unimplemented. The independent live
Al-Ki dates (Aug24 boarding, Aug28 map/storm, Sep10 arrival) must be compared
after those consumers are recovered; this proof does not explain or reproduce
that full calendar sequence yet.

Read-only Ghidra exports are under `local/ghidra/`: voyage-constructor/base/
bindings/message/progress/arrival and map-progress/weather-day/check/clear.
Reproduce with `ProbeVoyage.java`, `ProbeJournalUI.java` and
`ProbeFreshState.java`; source entrypoints are retained above. Persistent
annotations are recorded in COUNTDOWN.md after the owned save/reopen batch.
Selected NE2:2a8e sea-day rules now have independent original comparisons in
[SEA-DAY.md](SEA-DAY.md). Next concrete recovery is full3f6a timer/visual/rate
composition,2fea partner/journal notification and the three category1700
cutscene consumers, before claiming end-to-end sea travel or arrival fidelity.
