# Bounded initial Seattle population

**Observed source execution:** 96 original constructor cases reproduce the admitted actors, initial frame/anchor/rectangle, visibility/flip, two deadlines, and actual sprite-context list order for Seattle scenes1000/2000/3000/4000. The browser rule module matches these original outputs. This supplies initial poses; it does not establish a running scene lifecycle or the later animation loop.

The executable SHA256 is `9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`. Every selected resource retains archive offset, raw hash and normalized hash in [seattle-population-recovery-evidence.json](seattle-population-recovery-evidence.json). `prepare_seattle_population.py` separately exports all four SCNE records, their SCRP records, fourteen selected SPRTs and dependent ACEL/ASEQ/CBMP field tables. The generated metadata contains source fields rather than computed poses. Source media and raw images stay unchanged.

## Actual source path and ordering

Source addresses below are NE segment:offset. Ghidra12.1.4 maps NE1 to1000, NE2 to1008, NE3 to1010, NE6 to1028, NE13 to1060.

- Seattle scene constructor NE2:0002 creates global sprites through NE3:5e22/5f04, then reads Seattle arrival word through NE1:a78c(index0). When the word is zero it appends arrival journal event0 and starts global37500 sequence1. The bounded harness executes the constructors, getter and sequence start; it excludes the separate journal append.
- NE3:2268 loads the selected SCRP and NE3:2394 evaluates its condition pairs in order, stopping on the first false condition. Kind3 creates a child and its SPRT actor via NE3:274a; ticket clerk3001 uses derived NE1:c244, which installs its table after the generic constructor returns.
- Generic sprite NE2:e3b8 registers through manager tableNE6:706a slot34 → NE2:404c → context append NE2:dece. The harness executes these instructions and follows their links; it does not sort actors.
- After controller creation, scene0002 invokes NE2:e06a twice to move primary37500 and then secondary37501 after the current tail. Actual context head→next therefore contains admitted SCRP actors, then37500, then37501. Hit testing traverses the opposite order, as independently proved in [SEATTLE-NAVIGATION.md](SEATTLE-NAVIGATION.md).
- The first-visit date/visited-word mutation and arrival marking happen **after** this population stage. Downtown condition28 uses pre-entry word2ac through NE1:a7bc(index1). Passing its newly marked value would incorrectly select revisit actors on the first visit.

Static rendering consumer NE2:4290 reads context48 head0c and follows node next08. Visibleword28 and dirtybytes54/55 gate redraw. Manager+8 absent selects actor virtualslot0c with destination buffer+4, as previously established in [IMAGE-COMPOSITING.md](IMAGE-COMPOSITING.md). NE2:4466 follows the same head→next order for invalidation; NE2:3c8e is the manager update/draw/present caller. This supports drawing order but is not a whole renderer execution claim. Saved assembly exports are `local/ghidra/population-manager-slot{14,0c,1c}.asm.txt`.

## Selected initial poses

The following are source/native outputs with explicit partnerword312=ffff, propertyword320=0, pre-entry Seattle arrivalword292=0 and both clocks zero. Anchors are logical x/y; no OS window offset is applied.

| Scene | SCRP actors in context order | Bitmap/frame, anchor x/y |
|---|---|---|
|1000, Downtown visit2ac=0|1013,1003,1023|1011/0 (190,285);1001/0 (135,295);1021/2 (530,290)|
|1000, visit2ac=1|1014,1004,1023|1011/9 (260,285);1001/6 (230,295);1021/2 (530,290)|
|2000|2003|2001/0 (333,161)|
|3000|120,220,320,420,3001|120/2 (480,295);220/4 (350,300);320/1 (50,300);420/0 (225,310);3001/4 (248,155)|
|4000|4013,4023,4033|4011/0 (120,310);4021/0 (205,300);4031/0 (442,295)|

Each list is followed by37500/1 at anchor(110,100), rectangle TLBR(36,55,100,110), then37501/0 at(80,122), rectangle(122,80,124,149). With arrivalword292=1,37500 instead retains frame0, rectangle(100,110,108,117). Both global frame0 pixel images were independently decoded as all-zero; **first-arrival37500 frame1 is not empty** and cannot be omitted. Global constructors position frame0 with zero offsets; sequence1 changes to frame1 and invokes its ACEL offset. Applying ACEL0 to those initial global frame0 poses would be incorrect.

All selected SPRTs have header initial-sequence=-1 and callbackword+8=0. Their first schedule supplies sequence and interval. NE2:d556 starts that sequence and immediately executes its first step through NE2:d61e. ACEL frame setter NE2:d784 is called only when the new frame differs from current frame0; movement/flip also follows the original first step. Generic actors initially have visibleword28=1 and flipbyte2c=0. Source rectangle geometry remains signed16.

The two clock domains are distinct: NE3:61f6 calls **USER ordinal13 GetTickCount**, unsigned32 division by17; animation deadline is that quotient plus the first step's override or sequence duration. Scheduling uses **MMSYSTEM ordinal607 TimeGetTime >>4**, plus the first schedule interval. These original calls execute against explicit constant clock providers. Advancing either clock during construction, scheduler expiry/random choices, subsequent steps/successors and owner callbacks remain unsupported.

## Independent validation and substitutions

`verify_seattle_population_native.py` executes original controller and actor code in Unicorn2.1.4, with source NE fixups. Matrix: four scenes × arrival0/1 × per-scene visit0/1 × constant clock pairs(0,0)/(1000,1000)/(65535,65535) × successful allocator fill0/85 =96 cases. The48 allocator pairs have identical reported poses/order/controller records, and the explicit386-byte game-state buffer remains unchanged in all96 cases. Uninitialized actor snapshot bytes are excluded from the versioned expectation rather than treated as established fields.

Fixture boundaries are explicit:

- Allocator/free services substitute NE6:1ebe/1eac, with bounded successful allocation and requested fill pattern.
- Resource length/read NE1:7c88/7818 returns hash-verified, actual normalized resource payloads. Original resource-view/global memory wrappers still execute. KERNEL15/18/19 GlobalAlloc/Lock/Unlock are in-memory handle providers.
- CBMP cache getter NE2:9cd6 supplies typed metadata objects with actual source frame dimensions, source method tables, and rounded-four-byte stride. The cache constructor/bitmap decoder, pixel buffer initialization and renderer are **not** executed here. Initial pose consumers do not read pixel bytes.
- Controller owner and sprite manager are explicit source-shaped fixtures. SCNE installation, background loading, journal/date/visited/arrival state effects and full-world startup allocation are outside this harness. It is not proof of a complete fresh world state.

The additional memory-read instrumentation failed because it interfered with instruction-hook service routing. It was removed; no read-hook output establishes state-field dependencies. Dependencies above come from saved disassembly, actual getter requests and existing independent getter/reset proofs.

The bounded browser API `initialSeattlePopulation(source, inputs)` requires partnerffff/property320zero, pre-entry Downtown visit0/1, pre-entry arrival0/1 and both explicit clocks. Unsupported conditions, missing resources or callback/initial-sequence modes throw. Source ASEQ320 retains a successor4 outside its four-entry table: the selected initial sequence0/first step is valid and executes in the original, but the module does not follow that or any later successor. This discrepancy is not silently repaired.

`populationHitContexts()` reverses the actual list and requires a caller-provided **initialized native-layout indexed frame buffer including stride/padding**. It does not infer padding values. Original pixel hit NE2:e78a uses stride but compares its index to width×height; source geometry alone cannot establish what padding bytes contain. Rendering imported visible frame pixels and establishing exact native hit buffers are separate checks. Full initial scene pixels, native browser rendering, timer cadence and later interactive actors remain unverified; there was no browser or original UI access in this task.

## Reproduction

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python:tools python3 tools/verify_seattle_population_native.py \
 original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
 local/evidence/recovery-proof/seattle-population-native-20261014.json
python3 tools/prepare_seattle_population.py original/extracted/windows/YUKONRES \
 original/extracted/windows/YUKON.EXE generated/seattle-population-20261014.json
node tests/test_browser_seattle_population.mjs generated/seattle-population-20261014.json
```

The prepare destination must be fresh. To regenerate the versioned projection, rerun the native command with `--versioned-report docs/seattle-population-recovery-evidence.json --source-metadata generated/seattle-population-20261014.json`. This omits uninitialized snapshot bytes but retains all original reported poses and controller records. Node compares96 complete selected contexts/controller records against the versioned original execution oracle, not against Python pose calculations. It also checks reverse list conversion and rejection of partnered input.

`tools/yukonne_runtime.py` independently applies actual internal-selector and imported-ordinal fixup chains in memory, using explicit synthetic selectors and import entrypoints; OS/FPU fixups remain recorded/excluded. It rejects unsupported non-OS relocation forms. Its chain/type semantics were checked against official pinned [Ghidra SegmentRelocation source](https://raw.githubusercontent.com/NationalSecurityAgency/ghidra/Ghidra_12.1.4_build/Ghidra/Features/Base/src/main/java/ghidra/app/util/bin/format/ne/SegmentRelocation.java) and [NE loader source](https://raw.githubusercontent.com/NationalSecurityAgency/ghidra/Ghidra_12.1.4_build/Ghidra/Features/Base/src/main/java/ghidra/app/util/opinion/NeLoader.java). Independent Ghidra-loaded export audit checks6595 selector fields and326922 non-fixup source bytes with zero mismatches, recorded in [ne-runtime-loader-evidence.json](ne-runtime-loader-evidence.json).

For the audit, run `tools/ghidra/ExportLoadedSegments.java` read-only against the pinned YUKON.EXE program to `local/ghidra/population-loader-audit`, then:

```sh
python3 tools/verify_ne_loader_ghidra.py original/extracted/windows/YUKON.EXE \
 local/ghidra/population-loader-audit local/evidence/recovery-proof/ne-runtime-ghidra-audit-20261014.json
```

Source annotations for controller/SPRT and manager redraw were already persisted in earlier proofs. `tools/ghidra/AnnotatePopulation.java` added seven context/register/clock/manager caller names and comments. Apply and independent fresh read-only reopen match all14 annotation records; audit SHA256 `d82c9ef446c0f86cd3c54fcd0819c9afe63fa3f39747578495c1527201b7df27`. Root performed the serialized apply/reopen batch after its project backup; no concurrent project process was opened by this worker. Reproduce with `AnnotatePopulation.java apply <audit-path>`, save/close, then a separate read-only open with `AnnotatePopulation.java verify <audit-path>` against the pinned YUKON.EXE program.
