// Expected matrix hashes and opening cases come from original x86 execution.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {stepChoiceLinks, openLindaDialogue, responseAtPath} from '../web/rules/tree.mjs';
const json = path => JSON.parse(readFileSync(new URL(path, import.meta.url)));
const hash = data => createHash('sha256').update(data).digest('hex');
if (!process.argv[2]) throw new Error('Pass prepared asset directory');
const sourceGraph = id => JSON.parse(readFileSync(`${process.argv[2]}/TREE-${id}.json`)).graph;
const native = json('../docs/tree-links-recovery-evidence.json');
function* nodes(node, path = []) {
  yield [path, node];
  for (const [slot, choice] of node.choices.entries()) {
    if (choice.response) yield* nodes(choice.response, [...path, slot]);
  }
}
let count = 0;
for (const id of [3400, 2100]) {
  const graph = sourceGraph(id);
  const snapshot = JSON.stringify(graph);
  const allVisited = new Set([...nodes(graph.root)].flatMap(([, node]) => [node.record.offset, ...node.choices.map(c => c.record.offset)]));
  const rows = [];
  for (const [path, node] of nodes(graph.root)) {
    for (const slot of node.choices.keys()) {
      for (const result of [0, 1]) {
        for (const all of [false, true]) {
          const visited = all ? allVisited : new Set();
          const step = stepChoiceLinks(graph, path, visited, slot, result);
          rows.push([path, slot, result, all, step.nextPath, hash(Buffer.from(step.responseRecord?.text.bytes_hex ?? '', 'hex'))]);
          assert(step.visitedOffsets.has(node.record.offset));
          assert(step.visitedOffsets.has(node.choices[slot].record.offset));
          assert.equal(visited.size, all ? allVisited.size : 0, 'Caller visited state mutated');
        }
      }
    }
  }
  const reference = native.resources[`TREE:${id}`];
  assert.equal(rows.length, reference.cases);
  assert.equal(hash(JSON.stringify(rows)), reference.matrix_sha256);
  assert.equal(JSON.stringify(graph), snapshot, 'Source graph mutated');
  count += rows.length;
}
const linda = sourceGraph(3400);
const opening = json('../docs/conversation-open-recovery-evidence.json');
for (const test of opening.cases) {
  const result = openLindaDialogue(linda, test.before220, test.gate334);
  assert.equal(result.selectedRecord.offset, test.selected_offset);
  assert.equal(result.selectedRecord.voice_id, test.voice);
  assert.equal(result.flag220Word, test.after220);
}
// Actual direct Linda acceptance path, preserving selected source action/voice.
const direct = stepChoiceLinks(linda, [], new Set(), 2, 1);
assert.equal(direct.selectedRecord.offset, 0x29c2);
assert.equal(direct.responseRecord.voice_id, 3405);
assert.deepEqual(direct.nextPath, [2]);
const confirm = stepChoiceLinks(linda, direct.nextPath, direct.visitedOffsets, 0, 1);
assert.deepEqual(confirm.selectedRecord.action, [240, 4, 500, 0]);
assert.equal(confirm.nextPath, null);
assert.throws(() => openLindaDialogue(linda, undefined, 0), RangeError);
assert.throws(() => stepChoiceLinks(linda, [], new Set(), 0, true), RangeError);
assert.throws(() => responseAtPath(linda, [999]), RangeError);
console.log(`TREE module matches ${count} original link cases and ${opening.cases.length} original Linda opening cases`);
