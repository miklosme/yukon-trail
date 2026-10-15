# Selected Seattle dialogue predicates

This is source/native rule recovery, not live conversation or browser validation.
`docs/seattle-condition-recovery-evidence.json` records4,995 original outputs,
explicit full-sized state/settings inputs, fourteen graph identities and actual
record offsets/condition words, executed instruction bytes and routed calls.
ReportSHA256`cad227effa8e5da9afb575ce78483f2a7cfd249843e867e3af2c1c0a9eaaa51b`.
SourceEXE`9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`;
archive`438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`.

The source graphs are1,600,2100,3100,3200,3300,3400,3500,3550,3570,4300,4350,
4400,4450. Every nonzero condition pair in these graphs is represented in the
native matrix. This does not cover SCNE/SCRP/CONV conditions or the remaining
dialogue catalog. Callers must provide the actual conversation index and units
setting; speaker/scene associations are not automatically synthesized.

## Recovered behavior

All words below are raw unsigned16-bit inputs unless signedness is stated.
The indexed seen word is state`218+2*conversationIndex`. Index bounds0..60
match the recovered61-word flag array; representative actual indices and60
are tested. The dispatcher is original NE3:5118 (Ghidra1010; filebase1dde0).

| Kind | Supported behavior |
| --- | --- |
|0|Returns1 unconditionally.|
|2|Value1 when indexed seen word is nonzero; value2 when zero; other values false.|
|4|Requires seen word nonzero, then value1 when state30c is nonzero/value2 when zero.|
|7|Only merchant/index17 recovered. Requires seen23a nonzero. Paired predicate is318==17 and at least one of300/302/306 signedpositive; value1 if true/value2 if false. Other contexts explicitly unsupported.|
|11|Observed values107/108/109 test state300/302/306 respectively for exact zero. Other values explicitly unsupported.|
|26|Ship320 in1..3, with value equal to3−ship; other ship words false.|
|172|Value1 for nonzero units settings word30; value2 for zero. No default setting inferred.|

Kind7 is not simply a nonzero marker check. Original NE3:5238..5258 checks
seen then compares getter318 to the current index. Selected index17 follows
5266→52a2, reads inventory indexes3/4/6 via NE1:a744 and uses signed`>0`;
zero and wrapped negative values do not qualify. The special index9 branch is
unrecovered and rejected by this module. State318's broader meaning remains
unknown. Initial failed candidate formulas were corrected against original
outputs before this handoff; no candidate is retained as gameplay behavior.

New getter NE1:a040 is fifteen bytes, fileoffset`a4a0`:
`558becc45e06268b871803c9ca0400`, SHA256
`cb07910cfadb909a08c1bbcd5298c0a6b526758dc685cc29de8022f74b3f405a`.
It reads state318 without mutation. Already recovered NE1:a642, fileoffset`aaa2`,
reads30c: raw`558becc45e06268b870c03c9ca0400`, SHA256
`b87be1aa6e62973cc1d6ac6b37f921845e83d3adac0035387212cc94db69c915`.
NE1 maps Ghidra1000/filebase460. No flat executable address replaces NE offsets.

Kind172 runs NE3:5a7e..5a87: loads DS5314 settings pointer and compares its
word30 with0, then paired branch559b/57f5/5850. This is the same word used by
the journal's pounds/kilograms formatter. The actual merchant graph contains
two outfit-menu branches using this condition. Original settings initialization
and the full Management menu remain separate unknowns.

## Validation and limits

Python `tools/yukonconditions.py` and JS `web/rules/seattle-conditions.ts`
match all4,995 original returns and leave input state unchanged. The native
harness verifies full0x386-byte state and explicit settings buffers unchanged.
It uses zero/55/ramp synthetic backgrounds, unsigned/signed boundaries, indexed
flags, marker equality, individual inventory fields and ship/units values.
These are explicit fixtures; background bytes are not original startup defaults.
No complete world or browser lifecycle is inferred from the rule API.

All recorded instruction bytes were independently compared to the source EXE.
New FAR getter targets are checked against direct source NE selector fixups by
the bounded loader helper; source instructions remain unchanged and no getter
return is stubbed. The separate loaded-image/Ghidra audit now verifies6,595
internal selector fields and326,922 unaffected source bytes with zero mismatches;
see ne-runtime-loader-evidence.json. Imported and OS/FPU fields are excluded. Source OS/FPU fixups are not
executed by these predicate paths.

Additional memory-read instrumentation is excluded: a temporary prototype with
an extra Unicorn memory-read hook produced route/dependency failures for paths
that return correctly with the existing instruction hook alone. Those failed
instrumented outputs were not used to infer fields or predicates. Successful
proof uses the existing instruction hook, checked source getters and raw
instruction bytes; it makes no memory-read-trace completeness claim.

Unknown kinds, unobserved kind11 values and kind7 special contexts fail
explicitly. Actual initial/visible choice filtering, dispatcher caller context,
dialogue refresh, action results, visited links, voice timing and browser UI still
need integration and original comparison. There is no default-true fallback.

```sh
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_seattle_conditions_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  docs/seattle-condition-recovery-evidence.json
bun tests/test_browser_seattle_conditions.ts
python3 -m unittest tests.test_yukonconditions
```

Python3.14.5/Unicorn2.1.4/Node26.0.0 tested. Source and bulky analysis artifacts
stay ignored. `tools/ghidra/AnnotateSeattleConditions.java` applied two names/
comments without guessed signatures. A separate fresh read-only reopening
verified all five audit records including source identity, SHA256
`5339d327c67ffd395e87d9fff1552529d750202af3b7dd85c67aa0dadc2eedfd`.
Audits: local/ghidra/seattle-conditions-applied.tsv and matching verified.tsv.
Prechange backup: local/ghidra/conditions-population-before-20261014.tar.gz.
State30c retains the independently saved ticket annotation.
