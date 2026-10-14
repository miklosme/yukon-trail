# Selected Seattle sprites and hit regions

This is a bounded recovery of SPRT403 (Linda), ACEL400, ASEQ400, CBMP400, and the HSPT1000/4000 rectangle consumer. It is not a general animation engine or a completed Seattle milestone. Source identity, resource offsets/hashes, and independent results are recorded in [seattle-sprite-evidence.json](seattle-sprite-evidence.json). The EXE SHA256 is `9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`; archive SHA256 is `438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`. NE1/2/3/6 map to Ghidra 1000/1008/1010/1028 respectively; data13 maps 1060. Source resource normalization uses the recovered patterns in `tools/yukontransform.py`, leaving raw assets unchanged.

## Observed allocation and geometry

NE3:274a allocates and copies the normalized SPRT buffer: 38-byte header plus eight bytes per schedule, count at+36. Header+0 selects CBMP400; +2 selects ACEL400 and ASEQ400; signed anchor XY at+4/+6 is(-2,338); initial sequence+16 and click sequence+30 are both-1. Other header words remain unknown. SPRT403 schedules are(5,100,0,0) and(2,200,1,0). The interval word participates in clock-based scheduling, but its full timing/chance/repetition semantics are not independently validated.

The constructor installs table NE6:78d6 and stores SPRT ID+86, owner+88, copied SPRT+8c, ACEL+92 and ASEQ+96. It initializes+82=1 and+84=0. NE3:2a52 uses+84 as suspension of updates: with+82=1 it returns without hiding; with+82=0 and visible+28 nonzero it calls hide slot 10. It is incorrect to treat+84 as a direct visibility flag. The selected controller writes this word for kind3 (see Seattle rules).

Inherited drawing slot 0c is NE2:e554 and reaches the independently recovered zero-key compositor; see [IMAGE-COMPOSITING.md](IMAGE-COMPOSITING.md). Frame/offset setter slot 18 isNE2:e6ba; anchor setter slot 24 isNE2:e62a; movement slot 20 isNE2:e5e4. The rectangle stores top,bottom at+10/+14 and left,right at+12/+16, with anchorY/X at+24/+26. ACEL400 has three signed offset XY pairs:(5,-7),(10,-11),(10,-7). CBMP400 frames are121×112,124×108,124×112; frame 1 is the back-facing head/shoulders.

ASEQ400 has twelve eight-byte descriptors(startstep,successorsequence,defaultduration,stepcount), then a count 44 and twelve-byte steps(frame,dx,dy,unknownword,durationoverride,fliptoggle). NE2:d556 installs the descriptor; NE2:d61e advances steps, uses default duration when override is zero, starts successor when count expires, and invokes movement slot 20. Sequence 5=(12,2,10,4); steps 12..15 all=(1,0,-10,0,0,0). Its completed anchor is(-2,298). Sequence 2=(4,2,5,1) has a stationary frame 1 step. Timer cadence and successor execution remain unvalidated.

For frame 1, source geometry predicts logical rectangle left=-12,top=309,right=112,bottom=417. With observed scene origin(20,59), frame origin is(8,368). This forty-pixel rise comes from four source movement steps; it is not a viewport adjustment.

## Observed hotspot consumer

NE2:0c72 message 0x464 first checks sprite hits. Its HSPT fallback at0d4c scans sixteen-byte records after the leading count, ending at a rectangle with four zero words. The first four signed words are(left,right,top,bottom); the remaining words/dword are preserved as raw action fields. Both comparisons are strict: left<x<right and top<y<bottom. It selects the first matching record and passes its action payload to scene slot 10 at0de6. The loop uses the sentinel, rather than the leading count. The complete screen-coordinate dispatch and action semantics belong to the Seattle recovery; these primitive checks do not prove every interactive original control.

HSPT4000 has three nonzero rectangles plus sentinel:(0,500,120,270),(484,600,313,371),(532,550,303,398). HSPT1000 has ten nonzero records plus sentinel. Original ticket-office sign activation is an independent observation; rectangle records alone do not establish all sign/door/window behavior.

## Independent checks and reproduction

`tools/yukonsprite.py` preserves unknown fields and rejects malformed counts/ranges. Eight parser tests cover malformed input, signed fields, sentinel handling, boundaries and unsupported movement. Native verifiers execute original machine code under pinned Unicorn2.1.4, using synthetic segmented-memory harnesses rather than Windows APIs:

- `verify_hotspots_native.py`: 645 boundary/corner/intersection/overlap cases against NE2:0d4c..0df7; 494 for HSPT1000, 151 for HSPT4000;zero mismatches.
- `verify_sprite_geometry_native.py`:original anchor and four movement calls match the source-derived rectangle;36 suspension/visibility combinations also match original NE3:2a52 and NE2:e5b8. Constructor, clock and successor dispatch are excluded.
- `compare_linda_sprite_capture.py`:source-predicted frame 1 placement compared to original `local/evidence/seattle-reference-2026-10-13/krnl386_029.png` (capture hash in evidence). All 5,968 visible nonzero pixels match after independently checked display-index normalization and six-bit palette expansion.4,224 zero-key pixels and 3,200 clipped pixels are excluded. No alignment search is used. Underlying scenery, other actors, bubbles and the whole scene are excluded.

Run from repository root with the verified extracted `YUKONRES` and `YUKON.EXE` paths documented in original/README.md:

```sh
python3 -m unittest discover -s tests -p test_yukonsprite.py
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_hotspots_native.py ARCHIVE EXE local/evidence/recovery-proof/seattle-hotspots-native.json --id 1000 --id 4000
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_sprite_geometry_native.py ARCHIVE EXE local/evidence/recovery-proof/linda-sprite-geometry-native.json
python3 tools/compare_linda_sprite_capture.py ARCHIVE EXE local/evidence/seattle-reference-2026-10-13/krnl386_029.png local/evidence/recovery-proof/linda-sprite-pixels.json --scene-x 20 --scene-y 59
```

Native execution requires the permitted local Unicorn runtime; sandbox executable-memory restrictions may require the existing approved invocation. Resource exports and captures stay ignored. Unknown header fields, scheduling flags/chance, flip behavior across other sequences, full animation timing, hit dispatch coordinate projection, and other sprites are explicitly outside this result.

`tools/ghidra/AnnotateSprite.java` saved eight function names/comments and six fixed-width observed resource structures. A separate read-only reopen verified every field offset/type and every function annotation (audit hash and record count in evidence JSON). Names/types use observed fields only; function parameter signatures were not guessed. Backup: `local/ghidra/backups/sprite-before-20261013.tar.gz`. Reproduce with Ghidra 12.1.4 via `tools/ghidra/headless.sh`, `-process YUKON.EXE -noanalysis -scriptPath "$PWD/tools/ghidra" -postScript AnnotateSprite.java apply AUDIT`, then a separate process with `-readOnly` and `verify AUDIT`.

## Bounded browser module

`web/rules/scene-resources.mjs` reads source-normalized Uint8Array SPRT/ACEL/ASEQ/HSPT buffers, preserves unknown fields, and exports the selected strict hotspot fallback, explicit unflipped sequence completion, signed-word frame geometry and suspended-only visibility branch. It does not dispatch actions, intercept foreground sprites, project screen coordinates or advance clocks/successors. Suspension zero fails explicitly in the bounded suspension helper because it requires the unrecovered scheduling path.

`tests/test_browser_scene_resources.mjs` matches all 645 recorded original hotspot outputs, all five original geometry calls and all 36 original suspension outputs. The original verifiers now retain actual outputs and matrix hashes; the test inputs reconstruct normalized selected field metadata and must match original normalized resource hashes before JS parsing. Expected results come from original instructions, not Python model output. [browser-scene-resource-evidence.json](browser-scene-resource-evidence.json) records inputs, actual native rows, hashes, source identity and scope. Node checks do not constitute supported-browser presentation verification; no browser access was attempted for this work.

`tools/prepare_scene_resources.py` generates a fresh ignored directory containing normalized selected buffers and a provenance manifest, leaving raw media intact. Its `prepare(archive, executable, output, hotspot_ids=(1000,4000))` helper can be called by the main asset importer. The manifest retains original IDs, offsets, raw/normalized hashes, explicit buffer filenames, CBMP400 frame sizes and selected sequence metadata. No original bytes are embedded in the JS module; media remains in local generated assets.

```sh
python3 tools/prepare_scene_resources.py original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE generated/NEW-SCENE-ASSET-DIR
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_hotspots_native.py original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE local/evidence/recovery-proof/seattle-hotspots-native-browser.json --id 1000 --id 4000
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_sprite_geometry_native.py original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE local/evidence/recovery-proof/linda-sprite-geometry-native-browser.json
node tests/test_browser_scene_resources.mjs
```

The browser evidence JSON combines those native reports with source-normalized field metadata and the recorded Node run. These computations do not resolve the navigation/date timer context or create any UI.
