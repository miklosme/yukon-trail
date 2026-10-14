# Selected Seattle ticket and boarding recovery

This is a bounded source/native proof, not a completed departure or browser
playtest. `ticket-recovery-evidence.json` records source identities, archive
offsets/lengths/hashes, seven original recursive TREE parser comparisons and
the native matrices. EXE SHA-256 is
`9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`;
archive SHA-256 is
`438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`.
NE1/2/3/6 map to Ghidra1000/1008/1010/1028 respectively. Raw resource words
are normalized by the independently recovered original postread interpreter.

## Selected ticket and boarding voices

The seven actual graphs3500,3550,3570,4300,4350,4400,4450 reference56 nonzero
voice IDs. `ticket-sound-set-recovery-evidence.json` records every source graph,
record offset/text hash/voice ID, PSND source offset/hash and original PCM result.
All116,610 integer calls and7,476,546 PCM bytes match unchanged original routines;
zero mismatches. These voices are disjoint from the47 prior Seattle interview/
refusal voices. Header/terminal acceptance relies on the separate original proofs
in formats/PSND.md; this corpus comparison does not execute the full sound system.

Native report SHA256:
`f17d1cd71cbdfb1e25cc5acfdaabd9fcc3f3c636868d8e1bc03dfdc026bc052a`.
Ignored package:`public/game-assets/seattle-ticket-voices-verified-20261014`,
11CBMP/34frames/7TREE/56WAV. Manifest SHA256:
`b1d3a2e74a65fd193c28405d8eca9025f1abc1961af0ded4ec468ef0e496e9e0`.
Independent generated WAV checks have zero mismatches; exact exports are in
ticket-sound-export-evidence.json. Current server/main remains unchanged.

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_seattle_sound_set_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/ticket-sound-set-recovery-evidence.json \
  --tree 3500 --tree 3550 --tree 3570 --tree 4300 --tree 4350 --tree 4400 --tree 4450
python3 tools/prepare_seattle_opening.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  original/extracted/windows/YUF_____.TTF public/game-assets/FRESH-TICKET-VOICES \
  --voice-evidence docs/ticket-sound-set-recovery-evidence.json
python3 tools/verify_prepared_sound_assets.py public/game-assets/FRESH-TICKET-VOICES \
  docs/ticket-sound-set-recovery-evidence.json generated/FRESH-TICKET-EXPORT.json
node tests/test_browser_voice.mjs public/game-assets/FRESH-TICKET-VOICES \
  docs/ticket-sound-set-recovery-evidence.json
```

Prepare into a fresh directory. Playback onset, stopping, scheduling, volume,
native recorded waveforms and browser output remain untested for this corpus.

## Actual scene and dialogue binding

SCNE3000 references HSPT3000. Its first rectangle `(350,450,110,150)` has
action `(2,300,3500,0)`, so the clerk resource context is3500, category300.
The other person rectangle opens3100/category1700; it is not the clerk.
Factory NE1:4238 switch category300 branches426c→4148. At416c, resource3500
branches41ae; after allocation256bytes,41c8 calls NE2:216a. That constructor
calls generic NE1:0724 then installs NE6:668e, whose slot10 at669e resolves
to NE2:22c6. Scene3000's category200 message wrapper is a separate navigation
proof owned by the image worker; do not equate the generic scene test fixture
with that actual constructor binding.

CONV3500 is at0xbddf76,72bytes, SHA-256
`4ac029513fe49ca8006b41107cbe5b6212037ca6a5524488d85a242322700dfe`.
Its normalized first seven words are `(16,3002,3002,3002,0,0,0)`, followed
by count4. Header fields other than the firstword remain raw metadata here.
At byte16 begin four14-byte rows, each resourceword followed by three
condition pairs:

| Resource | Ordered conditions |
| --- | --- |
|3500|`(3,2),(0,0),(0,0)`|
|3550|`(3,1),(8,2),(0,0)`|
|3570|`(8,1),(0,0),(0,0)`|
|0|sentinel|

NE1:2c9e reads rows at CONV+10hex, tests up to three conditions at+12hex via
NE3:5118, advances14bytes and stops at zero resourceword. It does not use
the countword as the loop bound. Condition3 reads partner312 with original
signed logic: negative→3500; nonnegative plus zero ship320→3550; otherwise
3570. Condition8 uses original getter NE1:a7f4, testing320 zero/nonzero.
Forty-two native selector cases include signed boundaries and preserve the
entire supplied state buffer.

Each selected TREE3500/3550/3570 has one initial override `(2,1)` at byte4;
root response is byte0x228. CONVfirstword16 indexes state218+2*16=238.
Generic constructor0724 selects initial text at0883 before marking the
conversation via a2e4 at0937. Thus previous238 chooses rootvoice3501/3551/
3571 ifzero, or override3500/3550/3570 ifnonzero; then238 becomes1 only if
gate334=0. Fifty-four original condition/getter/mark cases compare full
sentinel state. Allocation, audio and full constructor execution are excluded.

## Fares and state mutations

TREE3550 offset0x5295019,31514bytes, SHA-256
`e88e180d29fa3b67fd6f9614ff2aaad163c5d664bf503b1ef621b5afbfd0428f`.
These are the original raw choice paths from the root; all confirmation
conditions are `(0,0)`, links4 and actions `(250,shipchoice,cost,0)`:

| Root path | Confirmation offset | Ship | Cost for two | Shipword320 | Destination322 |
| --- | --- | --- | --- | --- | --- |
|`1,0,0`|2132hex|Al-Ki, choice254|80|3|9000/Skagway|
|`1,1,0`|2e0ahex|Rosalie,255|60|2|9000|
|`1,2,0`|3ae2hex|Willamette,256|40|1|9000|
|`2,0,0`|4e26hex|Alliance,251|80|3|5000/Dyea|
|`2,1,0`|5afehex|Yosemite,252|60|2|5000|
|`2,2,0`|67d6hex|Eliza Anderson,253|40|1|5000|

NE2:22c6 handles250 at2374 and calls21ae at2388 with the action's fare and
shipchoice. The original switch at21f6/2206 maps251..256 to320/322 using
NE1:a3bc/a3e0. Both setters obey gate334; a3bc also dirties DS52fcobject+54.
At2221 an optional display-cache lookup927d can clear returned object+8a.
Then21ae calls original a184 with signed negativefare/slot0, ignores its
return, calls a184 with+1/slot5 (inventory304), and returns1. There is no
affordability check in this recovered handler, and no date/journal call.
If funds are insufficient, original money mutation can return0 and preserve
cash/bank while the fare handler still sets ship/destination and increments
ticket inventory. This is native routine behavior; a naturally reached live
Seattle insufficient-fare case has not been captured. Do not add a refusal
guard to this routine or claim that all surrounding UI paths were tested.

All mutations obey gate334. Inventory arithmetic wraps16bits and clamps a
negative signed result tozero. Its count is incremented by1, not2, despite
the dialogue selling two passengers' tickets. Native3,960 full0x400-byte
sentinel comparisons cover six source fares, cash0/39/40/59/60/79/80/422/
32767/32768/65535, bank0/20/80/32767/32768/65535, ticket0/1/32767/32768/
65535 and gate0/1. Matrix SHA-256:
`f4d1cd6f0f45f82e2356cae1ac261359fcc408de05634484f0b4c2e72424939e`.

The information choice3550+55e action `(260,261,3100,0)` queues category1700
resource3100 through22c6/238e and original4dba; argument261 is unused there.
Schedule rendering and the check-with-partner230/238 branch remain outside
this bounded fare implementation.

## Wharf selection and departure request

HSPT4000's first rectangle `(0,500,120,270)` invokes `(325,0,0,0)`.
NE2:0890→09c4 reads signed inventory304 via a744slot5. If positive, destination
322==5000 opens base4300/category300; every other destination opens4400.
If inventory is zero or negative, original NE6:2a28 RNG runs once; odd output
opens4300, even4400. This uses the explicit original32-bit seed; no OS seeding
is inferred. CONV4300/4400 then select base TREE4300/4400 when ship320=0 or
TREE4350/4450 when nonzero, using ordered condition8/2 then8/1. Six hundred
and thirty native dispatch/RNG/CONV cases preserve the full state, match
OpenScene arguments at the Windows creation boundary and match seed changes.
There is no inserted predicate requiring ship and ticket words to agree.

TREE4350 at0x52dfa8f and TREE4450 at0x52e8b41 are7950bytes each, SHA-256
`a6b20079f099005e5f62c98b29b8b4b586a9d2f6d80b2bf429d13b22a6144b7a`
and `0d63bc3092995e2703b8700b1e9b53972a3e07be563547f93a0f7ea9c5f5f554`.
Both rootresponses are byte0x33a. The three identical “Yes. Here are our
tickets.” raw choices use condition26/0,26/1,26/2. Original5118 maps ship320
3→value0,2→value1,1→value2; other words fail. Forty native condition cases
include invalid words and confirm exact equality. The next confirmation
actions are at670/cdc/1348hex, respectively `(320,0,0,0)`, `(320,7,0,0)`,
`(320,14,0,0)`. Their text identifies ready now/about a week/about two weeks.
Initial overrides `(4,2)` and `(2,1)` are checked in that order. CONV4300
firstword12 indexes state230; CONV4400firstword11 indexes22e. Condition4/2
requires prior conversationseen nonzero and rawstate30c zero via NE1:a642
(bytes558becc45e06268b870c03c9ca0400); then2/1 tests priorseen nonzero.
Thus freshseen0 selectsroot826; seen/nonzero with30c0 selectsrecord4;
seen/nonzero with30cnonzero selectsrecord278. Generic constructor selects
before markingseen1 gated334, as above. Sixty-four original contexts (128
condition checks plus64mark calls) compare all suppliedstatebytes and selectedrecords.
The broader meaning of30c remains unknown; it is not substituted with344.

Derived22c6 delegates320 to generic NE1:1250 branch1340. It decrements
inventory304 with a184(-1,slot5), obtains the actual parent through manager
stack search3e6a and calls NE2:100e: parent+0e=1, eight requestbytes copied
to parent+10. Raw opcode8eda at1028 is **MOV DS,DX**, even though this pinned
Ghidra assembly export misleadingly renders the registers reversed. Original
native execution confirms the far source copy; follow bytes/callers, not that
displayed mnemonic.

If delay0, handler sets state33a=0 via a530 (gated334) and queues manager
`(1,400,31000,0)` through4dba. If delay7/14, it queues `(3,0,0,0)` to close
the dialogue. Manager pending+2 becomes1 and actionbytes+4 are copied.
Thirty-six native comparisons run the actual derived/base dispatch, money,
parent lookup, local copy and manager queue; all state/parent/manager bytes
match across delays0/7/14, ticket0/1/2/32767/32768/65535 and gate0/1.
Matrix SHA-256:
`4b9dac72cad8a0df24e84137c1d1a886eb2e3557244017a721f479a4962ce9bf`.

Pending scene callbacks later consume parent+0e through0c72 and0890. The
nonzero320 action calls1036 to create the countdown animation. This later
Windows/timer path and eventual voyage31000 execution remain unimplemented;
the source request is not treated as completed travel or a guessed date jump.

## Observed reference and limitations

The independent original worker recorded `101` journal August24/$422/2400lb,
`105`–`108` clerk/Al-Ki80/“Have a safe journey”, `111` journal
August24/$342/2400lb with ticket visible. `118` recognizes the Skagway ticket,
`119` identifies Al-Ki ready to sail, and `120` after “OK! Here we go!” shows
the map on August28. `129` lists August24 boarding, August28 storm,
September10 Skagway arrival and September11 current entry. This source/live
scope supports the successful fare and immediate-board request; native hidden
state is not inferred from the journal.

Finalized captures `krnl386_003.avi` SHA-256
`3fb3aa4584a7fe275e9ce86c409bbb18be809fc3f6311f5e0493c546871e089f`
and `krnl386_004.avi` SHA-256
`9b0c2086ee7d6c15664ebf3214e3a5beda7a9195705fbb2f9a6c079c61236bd2`
remain in `local/evidence/seattle-reference-2026-10-13/`; their provenance
and live observations are in `white-pass-reference-evidence.json`. The blind
Dyea/Yosemite60 report is a separate live lead; this proof establishes its
source fare/7 request, not an independently timed wait or voyage comparison.

No browser input, UI rendering, audio playback, save continuation, schedule,
reservation correction, ticket refund, delayed departure, journal addition,
voyage random events or destination arrival is claimed complete here.

## Implementation and reproduction

`tools/yukonticket.py` and `web/rules/ticket.mjs` require explicit original
words/buffers. They expose clerk selection/opening, six selected source fares,
Wharf dispatch/RNG selection, ship-choice predicates and boarding queues.
Whole state bytes are preserved, unsupported actions fail. The shared
recovered money/RNG adapters do not create game defaults. Graph inputs for
the clerk opening API must retain source speaker16 and condition2/1.

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_ticket_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/ticket-recovery-evidence.json
/opt/homebrew/bin/node tests/ticket-oracle.mjs
python3 -m unittest tests.test_yukonticket -v
```

Unicorn2.1.4 executes original bytes with far selectors relocated. Only the
optional GUI cache is null and OpenScene is an argument boundary; no rule,
condition, RNG, parent search or copy is stubbed. Seven TREE graphs additionally
run original1:1c56/1d88 with bounded allocator only, comparing all response/
choice metadata, copied text, parent links and consumed extent.

Ghidra12.1.4/JDK21 backup:
`local/ghidra/backups/tickets-before-20261014.tar.gz`. `AnnotateTicket.java`
saves eleven function names/comments and the actual purchase switch body;
`ProbeTicket.java` exports branches/table/setters. Apply and independent fresh
read-only verify audit both hash
`8a81b90d08f8ef15c982d010aeaed2e611bc2e9b231302ba49e06a79ad979ac7`.
Commands:

```sh
tools/ghidra/headless.sh "$PWD/local/ghidra" YukonTrail -process YUKON.EXE \
  -noanalysis -scriptPath "$PWD/tools/ghidra" \
  -postScript AnnotateTicket.java apply local/ghidra/tickets-applied.tsv
tools/ghidra/headless.sh "$PWD/local/ghidra" YukonTrail -process YUKON.EXE \
  -noanalysis -readOnly -scriptPath "$PWD/tools/ghidra" \
  -postScript AnnotateTicket.java verify local/ghidra/tickets-reopened.tsv \
  -postScript ProbeTicket.java local/ghidra/ticket-switch.asm.txt
```

Next concrete consumer work is local pending callback→1036/countdown
completion and voyage31000 constructor/transition.
The root owns browser integration and STATUS; Ghidra was released to the
image worker after the completed save/reopen session.
