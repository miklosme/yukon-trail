# Archive postread word transformations

Checked 2026-10-13. **Observed:** the Windows archive reader transforms selected
resource buffers after loading them. The startup registry and all eight switch
operations are recovered from original instructions. A bounded Python model
matches the complete original transformation routine on 1,274 actual registered
records. This is byte normalization, not a recovered scene/dialogue engine or
evidence that SCRP is a general-purpose script VM.

## Sources and addresses

`YUKON.EXE`: SHA-256
`9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`.
`YUKONRES`: SHA-256
`438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6`.
Source paths are the verified files under `original/extracted/windows/`.

| Operation | Original NE | Ghidra | Source file offset |
| --- | --- | --- | --- |
| Startup registration pushes | `0001:677f–6a25` | `1000:677f–6a25` | `0x6bdf–6e85` |
| Register pattern | `0001:83e4` | `1000:83e4` | `0x8844` |
| Transform registered buffer | `0001:8462` | `1000:8462` | `0x88c2` |
| Switch table | `0001:85ae` | `1000:85ae` | `0x8a0e` |
| Swap16 / swap32 helpers | `0006:60ae/60c2` | `1028:60ae/60c2` | `0x4b06e/4b082` |

Context count is word `+70a`; registry rows begin `+7a`, stride `54` hex.
Each row has a logical tag dword and signed-word pattern terminated by zero.
Registration reads literal stack arguments, copies the words and appends zero.
The transform searches for the logical tag and leaves an absent tag unchanged.
CBMP and PSND are absent from the inspected startup registry.

## Original switch behavior

| Word | Branch NE1 | Observed operation |
| --- | --- | --- |
| -1 | `850e` | Advance cursor one byte |
| -2 | `851e` | Swap a word, advance two bytes |
| -3 | `8530` | Swap a dword, advance four bytes |
| -4 | `8542` | Swap word; retain its value and current pattern index as the single loop slot; advance two bytes |
| -5 | `8560` | Decrement retained word with 16-bit wrapping; repeat body when result is signed-positive |
| -6 | `8572` | Advance cursor 256 bytes |
| -7 | special path `84d4` | When first pattern word is -7, swap all payload words |
| -8 | `8578` | Consume next pattern word as signed skip amount |

After each ordinary operation the original compares the cursor with the end
pointer. It returns when the end is reached, otherwise advances the pattern
index and returns on a zero terminator. Loop bodies execute once before -5;
a zero count does not skip the first body when data remains. There is one loop
slot, not a general nested-loop stack. Unrecognized words fall through without
advancing data in the original. The bounded importer rejects unsupported words,
nested repeats and out-of-bounds reads/skips rather than duplicating unsafe
malformed-buffer behavior.

## Startup patterns

Actual logical tags include **ACTS, ANMS and SPRT**. These correct earlier
transcriptions CATS, AMSN and TRSP in ARCHIVE-CONSUMERS.md. Original startup
execution and raw push decoding agree on the corrected values. ACTS/ANMS/PRRS
have no record group in the supplied archive; presence in this registry does
not establish the contents or role of those types.

| Tag | Registration NE1 | Pattern words |
| --- | --- | --- |
| ACTS | `6794` | -2,-2,-3,0 |
| ANMS | `67bc` | -2,-2,-2,-2,-2,-3,0 |
| SCNE | `67e1` | -2,-2,-2,-2,-2,0 |
| HSPT | `6812` | -4,-2,-2,-2,-2,-2,-2,-3,-5,0 |
| PRRS | `6849` | -4,-2,-2,-2,-2,-2,-2,-2,-2,-3,-5,0 |
| SCRP | `6880` | -4,-2,-2,-2,-2,-2,-2,-2,-2,-2,-5,0 |
| SPRT | `68d8` | -2,-2,-2,-2,-2,-2,-3,-2,-2,-2,-2,-2,-3,-2,-2,-2,-4,-2,-2,-2,-2,-5,0 |
| TREE | `6912` | -2,-4,-2,-2,-2,-2,-3,-2,-2,-2,-6,-5,0 |
| CONV | `6958` | -2,-2,-2,-2,-2,-2,-2,-4,-2,-2,-2,-2,-2,-2,-2,-5,0 |
| ASEQ / ACEL / WRLD | `6971/698a/69a3` | -7,0 |
| FNTL / CSTR | `69bc/69d5` | -2,0 |
| FMAP / SMAP / CMIN | `69ee/6a07/6a20` | -7,0 |

Consequences are bounded: CSTR changes only its count word; TREE preserves
256-byte string fields while swapping selected numeric fields. Type semantics
and field meanings still require consumer traces. Do not reinterpret every
payload as little-endian words merely because some words are swapped.

## Implementation and checks

`tools/yukontransform.py` verifies executable/archive identity, extracts patterns
from the actual startup instructions, normalizes explicitly requested records
and records raw/normalized hashes. Raw exports remain distinct and unchanged.
It refuses an existing output directory and decodes all requested inputs before
writing results. Nine tests use independent byte expectations, including signed
skips, fixed string-byte preservation, the zero-count body and bounds failures.

`tools/verify_transform_native.py` executes original startup registration,
NE1:8462 and both original swap helpers in pinned Unicorn2.1.4. It relocates
only the far-call selector operands to synthetic scratch segments; no behavior
or Windows API is stubbed. All17 extracted patterns match original registration.
Six synthetic branch cases and all1,274 positive registered source buffers up
to60,000 bytes match the model, zero discrepancies. Buffer-overrun guard bytes
are checked. This is full bounded routine execution, not just copied arithmetic.

Three records are explicitly outside that native comparison: empty TREE39 and
WRLD39000/39001, each84,784 bytes. The bounded model rejects TREE39's required
first word; its empty archive record remains valid in the index. The model's
whole-word transform accepts both WRLD records, but their original huge-buffer
selector behavior is unverified. No live guest pointers or OS fixup constants
were measured, and the native harness does not cross a64KiB far-buffer boundary.

The model acceptance census is1,276 accepted /1 rejected registered records;
it is separate from the1,274-record native comparison. Full ignored census
metadata and selected export hashes are summarized in
[postread-recovery-evidence.json](../postread-recovery-evidence.json).

```sh
python3 tools/yukontransform.py original/extracted/windows/YUKONRES \
  original/extracted/windows/YUKON.EXE generated/postread-proof-20261013 \
  --key TREE:3400 --key TREE:616 --key SCNE:4000 --key CSTR:505 --key HSPT:4000
PYTHONPATH=local/tools/unicorn-2.1.4-python python3 tools/verify_transform_native.py \
  original/extracted/windows/YUKONRES original/extracted/windows/YUKON.EXE \
  local/evidence/recovery-proof/postread-all-bounded-20261013.json --all-bounded
python3 -m unittest tests/test_yukontransform.py -v
```

Python3.14.5 / Unicorn2.1.4 / Ghidra12.1.4 / project JDK21 were used. Native
verification now succeeds in the root execution context with current full
access; previous sandbox executable-memory limitations remain historical.

## Persistent analysis

Backed up project to `local/ghidra/backups/postread-before-20261013.tar.gz`,
disassembled the formerly missing switch cases, updated the two existing
postread comments and archive-reader comment, and preserved all names/types.
Fresh-process reopening retains both audit sets, byte-identical to apply:

- Recovery40 records SHA-256 `5719a8d0b23ce3fa08dfbaa4019d2ebf8f927f29f6518459c4d910794ad40f2d`.
- Archive47 records SHA-256 `63a78e28481210b1230b2b6fea784b7df3cfacff043ee15e4d036d1aeb18781b`.

The earlier hashes in CBMP.md/ARCHIVE-CONSUMERS.md describe historical comments.
Their annotation scripts now expect the supported updated descriptions. No
guessed signatures were installed. Reproduce read-only switch exports using
`ProbePostread.java OUTPUT_PATH`, and audits using `AnnotateRecovery.java verify`
and `AnnotateArchive.java verify` with the documented headless command style.
The backed-up writable apply also saved the newly disassembled switch cases.

Next work: interpret selected normalized scene/dialogue/hotspot fields through
their original consumers, and resolve TREE39 loading and large WRLD behavior
when those paths are required. Word normalization alone is not game fidelity.
