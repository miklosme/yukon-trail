# Seattle client input and navigation

## Evidence and scope

Observed source execution, not a live UI playtest: `tools/verify_navigation_native.py` executes unchanged bytes from `YUKON.EXE` SHA256 `9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`. It uses Unicorn 2.1.4 with synthetic segmented objects and initialized resources. `docs/navigation-recovery-evidence.json` preserves 1,231 common-handler outputs plus302 actual ticket-office-handler outputs, source resource hashes/offsets, call routing and fixture inputs. Output rows SHA256 is `b5d0b5c7c796596066606176b3237876694eea07195952a1536bb7124010f386`. Archive SHA256 is `438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`.

`web/rules/seattle-navigation.ts` matches all1,533 recorded outputs. This proves bounded event forwarding, sprite interception, HSPT fallback selection and opcode1–3 queue copying. It does not prove Windows message delivery, actual scene sprite state, scene teardown/construction, scheduling, deferred actions, dialogue or other opcode consumers. Browser access remains blocked; these are Node CLI comparisons, not browser presentation checks.

## Original callers and coordinate contract

NE1:5258 registers WndProc NE1:61b8 (Ghidra1000:61b8; segment file base0x460). Mouse down messages0x201/204/207 become game event0x464; up0x202/205/208 become0x46e. Signed x/y words from Win16 LPARAM pass unchanged through NE1:3c28 to Seattle virtual message handler NE2:0c72 (Ghidra1008:0c72; file base0xf2c0). Screenshot origin(20,59) belongs to the observed original client viewport; this game code does not subtract it from client input.

DS:5330 consumes and clears the next button event when nonzero. Scene manager DS:0090 suppresses forwarding when its busy word or null current-scene pointer is set. Common Seattle DS:1188 countdown skips click dispatch. Derived ticket-office handler NE1:bfe0 does not apply that gate to button464; use explicit `handler:'ticket-office'` for scene3000. The bounded module requires these words explicitly; a nonzero deferred scene action is unsupported because another source branch flushes action+10.

An earlier screenshot hypothesis assigned guest(70,205) to HSPT1000 record9. With the observed client origin, client(50,146) selects **record8**. The original tester's arrival at the ticket office supports that observed action; it is not proof of every surrounding pixel.

## Sprite interception precedes HSPT

NE2:3bea traverses context DS:0094+48 from list tail toward previous nodes. Node rectangle edges are signed and inclusive. Admitted nodes call sprite virtual slot28, NE2:e78a. This method reads the cached frame dimensions and initialized buffer through NE2:4d52/4d7a → NE3:1132/11a6. It computes signed16 `(y-top)*stride+(x-left)`, checks against `width*height` (not stride*height), then tests the indexed byte against zero. It does not read visibility word+28 or rendering flip byte+2c. A presentation visibility filter or flipped hit mask would therefore change the source behavior.

The original oracle includes121 complete sprite pipeline cases using an explicit cached8×8 frame and mask, resulting in32 hits and89 misses. These are synthetic geometry fixtures, not inferred active Seattle sprites. Ordinary cached buffer handle0 avoids Windows locking; locked handles and signed-word overflow/negative offsets remain outside this bounded module.

Any sprite hit prevents HSPT fallback. Object IDs0x927c/927d queue `(1,500,0)`; object200 reaches the original dialogue boundary (not executed in this oracle); other IDs produce no action. The module requires an explicit source-ordered sprite list. Passing an empty list for an unknown real scene is not a valid integration.

## Source navigation action mapping

The normalized HSPT consumer uses strict signed rectangle edges, first match and a zero-rectangle sentinel. Scene NE2:0002 loads HSPT from SCNE word2 and SCRP word3; SCNE2000 word1=0 does not mean it lacks hotspots.

| Scene | HSPT records | Original action |
|---|---|---|
|1000|0–2|`(1,200,4000)`|
|1000|3–6|`(1,200,2000)`|
|1000|7–9|`(1,200,3000)`|
|2000|0–3|`(1,200,1000)`|
|3000|0|`(2,300,3500)`|
|3000|1|`(2,1700,3100)`|
|3000|2|`(1,200,1000)`|
|4000|0|`(325,0,0)`; consumer outside this oracle|
|4000|1–2|`(1,200,1000)`|

NE2:0890 forwards opcode1–3's exact eight bytes through NE1:4dba → NE6:28c0 to manager pending word+2 and action+4. Static caller evidence NE1:3c7a →4238, category200 jump4258 →4a10 selects constructor NE1:bf82 for3000 and NE2:0002 for1000/2000/4000. `queuedSeattleScene` exposes only that bounded mapping. The full queue consumer and constructors are not part of the1,231-case oracle. Derived ticket-office constructor NE1:bf82 calls NE2:0002 and installs table NE6:624a: message slot4→NE1:bfe0, action slot10→NE2:0890. The actual handler repeats hit/HSPT dispatch for464 without the common countdown gate; up46e delegates0c72. A further302 original cases execute this actual handler, including121 cached-frame interception cases. Modal46b scheduling and full constructor lifecycle remain outside the oracle.

## Conservative source sprite census

`tools/inspect_seattle_sprite_bounds.py` records SCNE/SCRP/SPRT/ACEL/ASEQ/CBMP resource identities and every frame rectangle in `docs/seattle-navigation-sprite-bounds.json`. It includes all controller kind3 children except source condition(3,1), independently recovered as false for partnerwordffff (the independently recovered fresh reset word). Every other condition is conservatively admitted. All physically stored ASEQ movement vectors are considered; no active frame, timing or successor interpretation is guessed. ASEQ320 has a successor issue, but all of its movement vectors are zero, so the stated axis bounds do not depend on its successor interpretation.

Six open navigation rectangles are separated from every admitted source sprite on at least one axis with zero movement. Global widget37500/37501 source constructors NE3:5e22/5f04 set anchors(110,100)/(80,122); their initial zero-offset frame0 and all ACEL offsets are included. The census is conditional on those source anchors being retained, partnerwordffff and no modal/journal/dialogue context. External anchor changes, different partners and actual scene population/order are not established by this census. Do not use these regions as a general scene-wide substitute for sprite interception. Observed global animation wrappers NE6:7b0a/7b24 test object+8a and call NE2:d61e; their movement therefore follows the included ASEQ steps. External anchor mutations remain outside this scope. Navigation annotations are saved and checked by a fresh reopen (details below).

## Reproduction

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_navigation_native.py original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE local/evidence/recovery-proof/navigation-native-20261013.json
python3 tools/inspect_seattle_sprite_bounds.py original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE local/evidence/recovery-proof/seattle-sprite-bounds-20261013.json
bun tests/test_browser_navigation.ts
```

The first command needs the approved local Unicorn execution profile on this host; restricted memory mapping otherwise raises SIGILL. It invokes no UI or guest filesystem writes. Original binary/resource bytes are unchanged, and only far-call selectors are routed. The Node test reconstructs source HSPT bytes and checks normalized hashes before comparing original outputs. Generated resource files and captures remain ignored.

Correction: an intermediate, unintegrated census incorrectly labeled condition(3,1) false for partner0. The original oracle returns1 for0 and0 forffff. The versioned census now excludes that condition only under the explicit fresh ffff scope; it makes no partner0 claim.

## Analysis persistence

Ghidra12.1.4/JDK21.0.12.1: `tools/ghidra/AnnotateNavigation.java` saves11 original entry names/comments without guessing function signatures. The backed-up apply and separate read-only reopen matched22 function/comment records; auditSHA256 `8c062351cdcee8d38fe537af271ae7f504d66b8f64cd968007037cccd23f74ef`. Backup: ignored `local/ghidra/navigation-before-20261014.tar.gz`. Reproduce with `headless.sh local/ghidra YukonTrail -process YUKON.EXE -noanalysis -scriptPath tools/ghidra -postScript AnnotateNavigation.java apply AUDIT`, then a separate `-readOnly` invocation with `verify AUDIT`. Source hashes are required by the script. The versioned script reconstructs annotations; audits, full source exports and the bulky project remain local.
