# Original journal presentation

This bounded source trace supplies geometry/font inputs for the browser journal. It does not prove native-versus-browser text rasterization or all journal interactions. Source identities, exact table words and addresses are in [journal-presentation-evidence.json](journal-presentation-evidence.json). The source EXE hash matches the existing verified extraction; NE1/9/13 map to Ghidra 1000/1040/1060. Read-only exports are `local/ghidra/journal-ui-constructor.c/.asm.txt`, `journal-font-callback.c/.asm.txt`, and `journal-inventory-enabled.c/.asm.txt`. Decompiler output was checked against disassembly; erroneous inferred signatures/stack arguments are not used as proof.

## Constructor and original controls

NE1:aea4 installs table NE6:61a0, gets CBMP37000 ataf9c and sets it as scene-manager background atafe3; then gets CBMP37001 atafe7. These source IDs support the independently observed journal art. CBMP37001 is composed through generic sprite constructor NE2:e3b8, frame setter slot 18 and anchorYX setter slot 24; inherited drawing uses the recovered zero-key path.

Done is an original child button: at NE1:b0cc..b0f3, class string NE13:0e99=`button`, label NE13:0e94=`Done`, ID10, style0x50000000, logical rectangle(x105,y355,width70,height30). Journal text is an original child Edit: atb0fb..b132, class NE13:0ea0=`edit`, ID20, style0x50a01044. The edit rectangle is loaded through DS4e32, whose source relocation selects NE9; NE9:0000 at file0x4f3e0 stores(x0,y0,width302,height340). With observed journal client origin(20,59), Done is at(125,414) and Edit at(20,59). Native 024 independently shows those controls in the expected regions. This establishes the original controls; no additional controls are proposed here.

The constructor sends Edit WM_SETFONT(0x30) atb14a..b157, sets a text limit0x27ff through message 0x415, focuses it, and later sends WM_CHAR(0x102) with 0x20. The reference worker independently observed editable journal text/caret behavior. Text editing and cursor behavior remain presentation requirements, not recovered changes to game progression.

## Inventory table and visibility

The static table starts at NE13:0df4 (file0x50214), with sixteen ten-byte entries: signed(stateindex,statecompare,bitmapframe,anchorY,anchorX). The frame word is accessed at0df8 and anchor pair at0dfa. NE1:b032..b037 multiplies ordinal by10; interpreting this as pairs with stride4 produces incorrect positions.

NE1:bb4c checks the first two words: stateindex=-1 is unconditional; indices 7/8 compare the state-reader result for equality with statecompare; other indices require a nonzero state-reader result. Constructorb085 skips disabled entries, andb095 skips a negative bitmapframe. The words and observed placements are preserved in the evidence JSON; state index meanings are the separate recovered Seattle state model.

Source positions match independent root pixel measurements in native 024:

| Table ordinal | CBMP37001 frame | Logical anchorXY | Native originXY | Root measured matching nonzero pixels |
|---|---|---|---|---|
|9|10|(301,78)|(321,137)|4,369|
|14|6|(450,253)|(470,312)|7,210 above occlusiony397|
|15|11|(468,338)|(488,397)|5,591|

Root retains its comparison report/capture provenance. These measurements are independent of this source table; they validate selected frame placement, not all table conditions/frames or whole-scene composition.

## Font construction

The constructor enumerates face `Yukon Font` via pointer NE13:0dee to string0de2 ataf32. Callback NE1:be32 compares the returned LOGFONT face at +18, sets the found flag and retains the LOGFONT pointer. When found, af52..af7e requests ten points by setting height to `-MulDiv(10, GetDeviceCaps(hdc,90),72)` and width to0, then calls CREATEFONTINDIRECT. Other LOGFONT style fields are inherited from enumeration; the current trace does not read the returned runtime weight/italic/charset values. If no matching face is found, af86..af8d uses stock object 13. See [FONT-EVIDENCE.md](FONT-EVIDENCE.md) for the exact supplied TrueType font identity.

Ten points is observed source intent. A thirteen-pixel height at 96 DPI is a conditional calculation, not an independently captured GETDEVICECAPS result. Browser loading, native hinting, text metrics, selection/caret behavior and final screenshot comparison remain pending. Dialogue font choice is not established by this journal trace.

`tools/ghidra/AnnotateJournalPresentation.java` saves three source-established functions and two observed resource structures. A separate read-only fresh reopening verified all names/comments/field offsets and fixed-width types (audit hash in evidence JSON). No inferred function signatures were installed. Reproduce using the pinned headless toolchain with `-process YUKON.EXE -noanalysis -scriptPath "$PWD/tools/ghidra" -postScript AnnotateJournalPresentation.java apply AUDIT`, followed by a separate `-readOnly` invocation with `verify AUDIT`. The ignored prechange backup is recorded in the evidence JSON.

## Reusable native capture comparison

`tools/compare_journal_capture.py` derives all three selected inventory origins directly from the source's sixteen-entry table, plus the Edit pane boundary from NE9:0000. It requires an explicit observed scene origin and palette0 RGB. It performs no candidate/alignment search and records source resource offsets/hashes, decoded/display index hashes, capture identity, tested regions and exclusions. Raw exports remain unchanged.

Against native024 (SHA256`33a1d9ae80b45736517bdbb7cc431f4f024b43fcf28eec4a6c2b254d6e1721b7`), the independently recomputed results match all four earlier measurements: CBMP37000 cloth source rectangle(400,0,190,200) gives38,000 pixels; CBMP37001 frame10 at(321,137) gives4,369 nonzero pixels; frame6 at(470,312) gives7,210 above nativey397; frame11 at(488,397) gives5,591. Total55,170 comparisons, zero mismatches. [journal-capture-comparison.json](journal-capture-comparison.json) records the reusable run rather than the temporary locator.

The inventory clip starts at native x322, the source-derived Edit right edge. For frame6 the entire region at/below frame11's source-derived top(y397) is conservatively excluded; this does not claim every lower guide pixel is actually obscured. Zero-key pixels are excluded from inventory, but background zero pixels are compared using the explicitly supplied runtime palette value. Text, native controls, sprite visibility conditions, underlay and full-scene composition remain excluded. Three synthetic comparison tests check clipping/key accounting, background zero/crop union, difference reporting and invalid bounds; source/native pixel evidence provides fidelity validation separately.

```sh
python3 tools/compare_journal_capture.py original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE local/evidence/seattle-reference-2026-10-13/krnl386_024.png local/evidence/recovery-proof/journal-source-layout-20261013.json --scene-x 20 --scene-y 59 --system-palette-zero-rgb 0,0,0
python3 -m unittest discover -s tests -p test_journal_capture.py
```

## Current status and complete inventory follow-up

[JOURNAL-STATUS.md](JOURNAL-STATUS.md) now records the original event4 gate/full-buffer formatter and all16 inventory selectors. The browser rules match147 original output buffers and1,584 native selector calls. This also distinguishes formatter bytes from the constructor's later EM_SETSEL/WM_CHAR20 requests and the destructor's gated WM_GETTEXT copy; actual Edit-engine behavior remains a presentation comparison.

## Independently saved Edit insertion

The constrained original Dawson probe saves JPRE at capture299, opens and closes
the journal once at300–302 without typing, then saves JPOST at305. Root parsed
both exact11,221-byte containers and independently compared every byte. Only
file offset4021 changes00→20; all902 state bytes and header bytes are identical.
Journal text grows3,040→3,041 bytes by a single ASCIIspace, distinct from its
existing trailing formatter space. Source constructor NE1:b1b9 sends WM_CHAR20
after selecting the end. Exact save hashes/text and limitations are retained in
[journal-edit-reopen-evidence.json](journal-edit-reopen-evidence.json).

The port now applies this insertion at Edit construction and captures it on
Done; it selects the end using the actual DOM value length after LF normalization.
`node tests/test_journal_edit_text.mjs` matches the independently saved before/after
text. Capacity insertion and repeated opening while already editing fail explicitly
because those original cases remain unverified. Browser caret/rendering comparison
and fresh-opening Edit bytes are still pending.
