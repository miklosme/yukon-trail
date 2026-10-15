# Journal status append and inventory selection

## Source and validation

Observed original instruction execution uses `YUKON.EXE` SHA256 `9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`, Unicorn2.1.4 and explicit initialized state/journal/settings fixtures. `docs/journal-status-recovery-evidence.json` preserves147 complete output-buffer cases,99 inventory contexts with1,584 original selector calls, three Edit-retention request boundaries, source fragments/table hashes and a capture094 comparison. These are source/CLI comparisons; no browser or original UI was controlled for this recovery.

The harness executes original NE1:c474 event4, NE1:dbe2 formatter, date/place/getter and string routines. Only successful platform malloc is replaced with bounded local memory; it records8-byte entry-object and255-byte text allocations. It stops after journal append and before temporary-object destruction. Clean gate cases return through the original function normally. Game state bytes are checked unchanged. Allocation failure, journal overflow prompts/retention and actual Windows Edit execution remain unsupported.

`web/rules/journal-status.ts` matches all147 output buffers and snapshot words, plus all1,584 inventory selections. `tools/prepare_journal_status.py` imports only verified source strings and the complete inventory table; parent asset preparation can call `source_data(executable_bytes)` without replacing existing generated files. No new controls or main integration are included.

## Opening and dirty gate

Journal presentation constructor NE1:aea4 calls NE1:c474 with event4 before populating the original Edit control. Event4 compares these journal-object cache words against the game state:

| Journal object offset | Cached field | Original state source |
|---|---|---|
|+00|day|state+28 through NE1:a68e|
|+02|month|state+2a; stored, **not compared** by this gate|
|+04|food|NE1:a744 index2 → state+2fe|
|+06|cash|NE1:a744 index0 → state+2fa|
|+08|gold|NE1:a744 index1 → state+2fc|
|+0a|dirty word|only equality with1 forces append|

It appends if day, food, cash or gold differs, or dirtyword==1. It always refreshes the cached day/month/food/cash/gold, including when no entry is appended. It clears the dirty word only on the append path. Values2/ffff do not force an append by themselves. Partner, inventory words, phase/year and location tuple are not directly compared by this branch. Matrix cases vary them independently; actual setters may have additional side effects outside these direct-input cases.

Journal text state constructor NE1:c2c2 allocates/locks0x2800 bytes, initializes the text NUL and dirtyword1, and clears cachedfood/cash/gold. It does not initialize cachedday/month in this function; no defaults for those are invented. Fresh/reset paths NE1:929e/9698 clear the text and set dirtyword1. The post-first-summary cache is independently known as `[23,8,0,350,0,0]` in `capture094.original_first_event4.snapshot_words`; integration after that summary needs no guessed pre-constructor day/month. Save/restore orchestration is separately documented; this recovery does not infer a complete restored UI lifecycle.

After the independently proven first Wharf→Downtown date advance23→24, the day difference produces a new status entry. Reopening with the same day/food/cash/gold and dirtyword0 produces no additional status entry. Raw journal text itself is never replaced by the event4 formatter: successful append retains its complete byte prefix, including user text and whitespace.

## Exact status formatting

NE1:dbe2 creates a255-byte entry. Existing nonempty journal text adds two CRLF pairs. Original date/place helpers supply month/day, phase-selected1897/1898 and selected region200/place-index0 Seattle text. Scene tuple word2 is not read by that selected place branch. Other regions/indices remain unsupported. Initial units-setting construction is not recovered; capture094's pounds text independently selects the zero branch for that observed scenario.

Source data13 fragments, with Latin1 byte mapping:

| NE address | Fragment |
|---|---|
|1106|`We have:\r\n      `|
|1117|` kilograms of food\r\n      $`|
|1133|` pounds of food\r\n      $`|
|114c|` in cash`|
|1155|`\r\n      $`|
|115f|` in gold`|

Food/cash are converted as signed16 decimal words. If settings object DS:5314 word+30 is nonzero, food is `trunc(signed_food*45/100)` and uses kilograms; otherwise it uses pounds. Gold adds the last line only if its signed16 value is positive. This differs from inventory gold visibility, which checks nonzero. Boundary cases32767/32768/ffff preserve those source distinctions. Each component is appended only when the combined entry length stays strictly below255. Full journal append is supported only below0x2800; the original overflow prompt/1000-byte retention path remains a precise unsupported boundary.

## Complete inventory table

NE1:bb4c evaluates all16 entries at NE13:0df4 (file0x50214), stride10 signed words `(state_index,state_compare,frame,anchor_y,anchor_x)`. Original getter NE1:a744 returns `state+2fa+2*index`. Index-1 is unconditional. Indices7/8 compare against the table's statecompare; every other index tests nonzero. The presentation constructor also excludes negative frame IDs. All16 source frame IDs are nonnegative.

The source table selects frames0/1/2 when index7 equals7/8/9, and frames3/4/5 when index8 equals10/11/12. Index3 admits frames14 and12; index6→13; cashindex0→10; foodindex2→9; index5→7; goldindex1→8; index4→15. Frames6 and11 are unconditional. These are exact source indices, not inferred names for unobserved equipment. All anchors and record order are preserved in the evidence and importer. Source selector behavior is compared over every index0..8 with0,1,7..12,32767,32768,ffff. Native inventory pixels for the three fresh visible frames remain the separate55,170-pixel comparison in JOURNAL-PRESENTATION.md; other inventory pixel states have not been live-captured here.

## Capture094 and editable bytes

Unchanged recorded `local/evidence/seattle-reference-2026-10-13/krnl386_094.png` independently shows arrivalAugust23, statusAugust23 and statusAugust24, food0/cash350, with prior entries retained. The original event0→event4→day24/event4 sequence produces those seven nonempty tail lines. Capture comparison excludes owner/header and strips invisible indentation/trailing whitespace; exact output bytes come from original code, not OCR. Event0→first event4 tail is119 bytes, SHA256 `6bce15cb4e07d7910fa5869e22e70c5cadb16b0fccc159304387e5c4d2de6220`; preserve evidence key `capture094.original_first_event4.text_hex`. The owner header constructor is not executed by this oracle.

A source byte discrepancy was corrected by the parent: arrival event0 ends `Arrived at Seattle. `, including finalASCII20. The formatter's final cash line has **no trailing space** for gold0. Original UI constructor later sets selection to the journal length through EM_SETSEL and sends WM_CHAR0x20 at NE1:b1b9. Actual Edit-engine insertion/selection behavior is a separate pending UI comparison; it must not be folded blindly into formatter text.

Nondeleting destructor NE1:b1ca and deleting entry NE6:60fc copy Edit contents into the journal text buffer via WM_GETTEXT(capacity0x2800) when DS:0df2==0, before destroying controls. For flags1/ffff the request is skipped. Original request-boundary execution records LPARAM pointing directly at journaltext+0e, wParam10240, message13 and the selected Edit HWND. That proves the caller contract, not the implementation of Windows Edit. The bounded browser rule accepts explicit NUL-free one-byte prior text and preserves it; capturing DOM edits on close belongs to presentation/platform integration.

## Reproduction and persistence

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python:tools python3 tools/verify_journal_status_native.py original/extracted/windows/YUKON.EXE local/evidence/recovery-proof/journal-status-native-20261014.json
bun tests/test_browser_journal_status.ts
python3 tools/prepare_journal_status.py original/extracted/windows/YUKON.EXE local/browser-assets/journal-status.json
```

Unicorn needs the approved local execution profile on this host because restricted memory mapping otherwise raises SIGILL. Original binaries, captures and generated assets remain unchanged/ignored. The importer refuses to replace generated output.

`tools/ghidra/AnnotateJournalStatus.java` saved seven original function names/comments and no guessed signatures. A separate Ghidra12.1.4/JDK21.0.12.1 read-only reopen matched14 records; auditSHA256 `4b0c087938b52e3e7bfcae9eadbe3e356088f0231484d4a278d31f625cc99893`. Prior backup: ignored `local/ghidra/journal-status-before-20261014.tar.gz`. Reconstruct with `headless.sh local/ghidra YukonTrail -process YUKON.EXE -noanalysis -scriptPath tools/ghidra -postScript AnnotateJournalStatus.java apply AUDIT`, then a fresh `-readOnly` call using `verify AUDIT`. Read-only exports are `journal-status-formatter`, `journal-state-item-getter`, `journal-edit-handler` and `journal-destructor` under local/ghidra. Segment mappings: NE1→1000/file0x460, NE6→1028/file0x44fc0, NE13→1060/file0x4f420.

Integration must use explicit known words for these bounded readers. The original state caller mallocs0x386 bytes then calls NE1:98ea→9900; no caller fill occurs between them, but that does not establish allocator contents or a startup RNG seed. Do not serialize a zero-filled reader projection as a complete original world. Journal/inventory readers do not use RNG-selected state314/316. Source activation must establish location34/36 separately.
