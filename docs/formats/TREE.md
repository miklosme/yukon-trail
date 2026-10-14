# Selected TREE dialogue records and consumers

Checked against Windows `YUKON.EXE` SHA-256
`9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`
and `YUKONRES` SHA-256
`438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`.
**Observed:** original recursive graph construction and selected choice links
match the bounded implementation. This is not a general dialogue VM or a
complete UI, condition or action catalog.

## Payload and graph

Apply the source TREE [postread transform](POSTREAD.md) first; the specification
below uses normalized little-endian words. The payload has four header bytes
(two words, selected speaker/context word and recordcount) and274-byte records.
Original text bytes remain unchanged by postread.

| Record-relative offset | Width | Observed selected use |
| --- | --- | --- |
| `+0` | 2 | Runtime record visit word; selected source0 becomes1 on choice processing. Other initial values retained. |
| `+2` | 2 | Choice absolute link level, compared with dialogue depth. Meaning for non-choice records retained without interpretation. |
| `+4` | 8 | Action: opcodeword, argumentword, operanddword. Model preserves four rawwords. Selected amounts use lowword with highword0. |
| `+0c` | 4 | Condition opcodeword and valueword. |
| `+10` | 2 | Voice resource ID passed to selected PSND path. |
| `+12` | 256 | NUL-terminated original text bytes. Space is nonempty; zero firstbyte is a terminator. |

`0001:1f02` / Ghidra`1000:1f02` copies up to five initial override records
while their text is nonempty, skips their empty terminator, and starts the
normal response graph. `0001:1c56` copies a response, then repeatedly calls
`0001:1d88` for choices until an empty choice-list terminator. Each choice is
followed by a nested response if its text is nonempty, or by an empty
no-child record. Nested responses use the same format. Native structures use
separate22-byte records (18 metadata bytes plus textfar) and88-byte nodes:
responsefar`+0`, ten choicefar slots`+4`, parentfar`+2c`, ten child-nodefar
slots`+30`. Both copy helpers advance the source by`0x112=274` per record.

`tools/yukontree.py` implements this bounded normalized graph, preserving
record byte offsets, metadata and text bytes. It checks count/length, NUL
termination, at most five overrides/ten choices, recursion bound64, missing
terminators and unsupported nonzero trailing records. All-zero trailing
records are retained by offset as metadata: the selected native parser stops
before them rather than interpreting another node. Text encoding is a
separate presentation decision; this parser does not recode it.

Selected resource provenance and original-parser results:

| Resource | Archive offset | Length | Raw SHA-256 | Result |
| --- | --- | --- | --- | --- |
| TREE3400 | `0x528dc69` | 14526 | `948242aaa095b020ee47f6b6df71d8a4abaeedb14517ab85e6d8feb105b0e57a` | 53records; one override; root`+228`;17response nodes;82allocations; trailing zero record`+37ac`. |
| TREE2100 | `0x522f6c7` | 24664 | `eabb9e6ed25f0ff36ebaffb6717c58ae41276ed605657da6d1267a3b36c7e353` | 90records; three overrides; root`+44c`;29response nodes;142allocations; no trailing records. |

`verify_tree_native.py` executes original `1c56/1d88`, strlen/strcpy/memcpy/
memset and recursion. Only allocation is replaced by a bounded zeroed
synthetic heap. All copied metadata/text, choice-child relationships, parent
links and consumed extent match the implementation. The independent selected
root offsets are explicit inputs; the archive loader/initial override copy
is not emulated here. Metadata: `docs/tree-recovery-evidence.json`.

## Selected UI, links and actions

The actual constructor `0001:0724` installs table`0006:609a` (Ghidra
`1028:609a`), with slot4→`0001:2468` UI handler, slot8→`0001:29d2` update,
slot10→`0001:1250` action dispatcher. The earlier base table`608a` contains
runtime stubs; it must not be mistaken for the concrete UI handler.

**Observed `0001:2468`:** in menu phaseword`+ce=3`, a valid click or keyboard
message maps a visible option index through original word array`+b6` to a raw
choice slot. It stores that choice's actionfar in dialogue`+26`, calls action
slot10 **first**, then passes its0/1 return to `0001:2fec`. Thus mutation or
refusal occurs before the subsequent link step. Opcode3/f0 clears the selected
player option afterward; no extra player-response stage is invented for those
exit operations. Mouse hit-testing, audio completion, timers, phase changes
and display calls remain separate presentation behavior.

`0001:2fec` marks the current response and selected choice word0 as1. On a
successful action, it exposes the associated child response text/voice and
executes that response's action. It then uses choice linkword and depthword
`+b4` (root1). If link≤depth, it walks parent`+2c`, decrementing depth until
depth<link; a null result exits. Non-root nodes with no unvisited, nonempty
choices rewind farther. Condition results do not enter that unvisited-count
loop. For link>depth, the native branch at`32a6` checks the child node's **first
option-response pointer**`+30`: if nonnull it descends and returns before
additional rewind; if null it keeps the current node and may rewind it. This
specific check matters for a leaf NPC reply and for already visited children.

`step_choice_links` implements this selected link behavior with explicit
current path, visited offsets, raw choice slot and action return. It returns
the next path (`None` exits), selected choice and any child response to show.
It does not execute actions, filter conditions, invent timers or render text.
All176 native comparisons pass:64 for Linda and112 for the merchant, spanning
every raw choice × action result0/1 × fresh/all-visited contexts. Native
`2fec` executes after original graph construction and stops before UI refresh
`1:35f8`; a synthetic child-action callback records its original eight-byte
arguments without applying game effects. This exposed two implementation
mistakes in forward rewind, which were corrected before the final comparison.
Metadata: `docs/tree-links-recovery-evidence.json`.

The direct selected Linda path is root`+228` (voice3401), choice`+29c2`
(link2), child response`+2ad4` (voice3405), choice`+2be6` (link1,
action`(240,4,500,0)`), child space response`+2cf8`, exit. Earlier nested
confirmation copies are at`+cdc` and`+1dfc`. The special partner dispatcher
`0002:22c6` handles opcode240 as established in [SEATTLE-RULES](../SEATTLE-RULES.md).

## Selected condition binding

The ordered initial selector `0001:2bc2` chooses the first available override
whose condition returns true, otherwise the root response. TREE3400's single
override at`+4` has condition`(2,1)` and voice3400. Original condition
`0003:5118` calls `0001:a774` at`0003:5a34`, passing CONV firstword4 as index.
Getter reads stateword`+218+2*4=220`. Nonzero selects the override; zero selects
root voice3401. Its broader flag-array meaning remains unknown.
`select_linda_initial_record` requires that explicit rawword; no flag default
is supplied.

TREE2100's whipsaw option at`+4af0` has condition`(11,109)`. The original
condition calls indexed getter`0001:a744` at`0003:5485` with slot6, returning
stateword`+2fa+2*6=306`. This option is available exactly when that word is0.
`whipsaw_option_visible` implements only this selected rule. Twelve original
condition/getter comparisons cover rawwords0/1/2/32767/32768/65535 for the two
selected conditions, with zero discrepancies and no state writes. All getter
arguments and far-call relocations are in `tree-conditions-recovery-evidence.json`.
Other conditions fail explicitly when not recovered; their names/numeric tags
alone establish no rules.

CONV source provenance: CONV3400 at`0xbddf4a`,44bytes,
SHA-256`fa7bf68e1568df7172bf2e3ea78890ff5f340d4708837f528740f7ce11ad4b8c`,
firstword4; CONV2100 at`0xbdd78c`,86bytes,
SHA-256`786015e9ba10842e8ce03156e8cea9bf031754712481c3fad5b66a1ea7c08ec4`,
firstword17. Source postread normalizes these words.

## Reproduction and remaining scope

Python3.14.5, pinned Unicorn2.1.4, Ghidra12.1.4/JDK21; original artifacts and
projects remain ignored. Native verifiers require executable-memory sandbox
approval already used for the other selected-code proofs.

```sh
python3 -m unittest tests.test_yukontree tests.test_yukonpurchase
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_tree_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/tree-recovery-evidence.json
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_tree_links_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/tree-links-recovery-evidence.json
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_tree_conditions_native.py \
  original/extracted/windows/YUKON.EXE docs/tree-conditions-recovery-evidence.json
```

Useful read-only exports: `dialogue-ui-handler`, `dialogue-choice-step`,
`dialogue-parse-choice`, `dialogue-slots-merchant`, `merchant-action`,
`merchant-purchase`, `merchant-constructor-persisted` under`local/ghidra/`.
`ProbeDialogueSlots.java` re-exports the relocated tables and bounded missing
consumer bodies before decompilation. `AnnotateTree.java` saves checked native
names/comments without guessed parameter types. Public asset distribution,
full original UI event execution, general conditions/opcodes, text layout and
all alternate dialogue contexts remain outside these proofs.

The eight-function `AnnotateTree.java` apply/reopen audit matches SHA-256
`37de887dda72f1968ebe2cd41f8cbf0527a7f3ab809cf5a274ea41e94fc32500`.
Backup before persistence:
`local/ghidra/backups/tree-purchase-before-20261014.tar.gz`.

## All-resource structural census and native response graph comparison

**Observed,2026-10-14:** the source archive contains510 TREE resources.
The bounded parser accepts509 nonempty graphs:2,400 response nodes,1,894
choice records,126 initial overrides, maximum nested response depth6. Their
nonzero voice references cover761 distinct IDs; every referenced PSND exists.
Raw action/condition opcode counts and per-resource source offsets/hashes are
in `docs/tree-census-evidence.json`. These numeric inventories do not assign
unrecovered gameplay meanings. Versioned metadata records aggregate references
and a per-record metadata digest; detailed exports remain reproducible/ignored.

`tools/verify_tree_census_native.py` then independently executes original
NE1:1c56/1d88 response recursion and copy/string routines on all509 nonempty
source graphs. Initial root offsets come from raw normalized empty-text
sentinels, independently of the model's graph. All2,400 response nodes and
10,479 allocations compare exactly: record words/text copies, child/parent
pointers, choice absence and consumed cursor extent; zero mismatches.
Only bounded synthetic allocation and established segmented routing are
substituted. Input stays below60,000bytes; heap stays in one checked segment;
each graph has an explicit1,000,000-instruction ceiling. The prior selected
verifiers retain their100,000 default. No Ghidra annotations changed here.

The one excluded resource is empty TREE39 at archive offset`0x52a96df`,
length0, SHA256`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
It has no response graph. Original loader/error handling for that empty entry
remains unknown; it is neither parsed as a default graph nor silently skipped
in the evidence.

Census SHA256`5a99bd9e255b738cba6d50fed521dd6c21c26551dc177e3c65a6d4a9fcf5051d`.
Native graph evidence SHA256
`2c28351db6fb4fc02e777599bef9867897a11e6500fbe03c199e5cdd5cb493b5`.
The reports independently agree on all509 source identities/counts/node totals.
This expands response construction proof; initial override loading, condition
evaluation, action dispatch, live choice visibility, speech and UI remain outside
this corpus proof. It does not establish full dialogue/playable coverage.

```sh
python3 tools/audit_trees.py original/extracted/windows/YUKONRES \
  original/extracted/windows/YUKON.EXE docs/tree-census-evidence.json
python3 tools/audit_trees.py original/extracted/windows/YUKONRES \
  original/extracted/windows/YUKON.EXE generated/tree-census-record-details.json \
  --record-details
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_tree_census_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/tree-census-native-evidence.json
python3 -m unittest tests.test_audit_trees
```

Python3.14.5/Unicorn2.1.4 were used. The standard-library census/tests do not
require Unicorn or source media fixtures. Native proof requires the unchanged
local extraction and existing approved instruction-analysis runtime.
