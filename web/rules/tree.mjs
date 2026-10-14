// Selected original NE1:2fec graph links and0724/a2e4 Linda opening order.
// Input is a source-derived TREE graph, preserving original record fields/bytes.
// Source/native scope: docs/formats/TREE.md and docs/SEATTLE-RULES.md.
// Condition filtering, action execution, platform/audio and GUI refresh excluded.
function word(value) {
  if (!Number.isInteger(value) || value < 0 || value > 65535) {
    throw new RangeError('Explicit original unsigned 16-bit word required');
  }
  return value;
}
export function responseAtPath(graph, path) {
  if (!graph?.root || !Array.isArray(path)) throw new TypeError('Source TREE graph and explicit path required');
  let node = graph.root;
  for (const slot of path) {
    if (!Number.isInteger(slot) || slot < 0 || slot >= node.choices.length || !node.choices[slot].response) {
      throw new RangeError('Unsupported response path');
    }
    node = node.choices[slot].response;
  }
  return node;
}
export function selectLindaInitialRecord(graph, flag220Word) {
  word(flag220Word);
  if (graph?.speaker_word !== 4 || graph.initial_overrides?.length !== 1 ||
      graph.initial_overrides[0].condition?.[0] !== 2 || graph.initial_overrides[0].condition?.[1] !== 1) {
    throw new RangeError('Only the selected TREE3400 initial override is recovered');
  }
  return flag220Word ? graph.initial_overrides[0] : graph.root.record;
}
export function openLindaDialogue(graph, flag220Word, gate334Word) {
  word(gate334Word);
  const selectedRecord = selectLindaInitialRecord(graph, flag220Word);
  return {selectedRecord, flag220Word: gate334Word ? flag220Word : 1};
}
export function stepChoiceLinks(graph, currentPath, visitedOffsets, choiceIndex, actionSuccess) {
  if (actionSuccess !== 0 && actionSuccess !== 1) throw new RangeError('Original action result 0/1 required');
  if (!(visitedOffsets instanceof Set)) throw new TypeError('Explicit visited record-offset Set required');
  const node = responseAtPath(graph, currentPath);
  if (!Number.isInteger(choiceIndex) || choiceIndex < 0 || choiceIndex >= node.choices.length) {
    throw new RangeError('Choice slot outside recovered node');
  }
  const choice = node.choices[choiceIndex];
  const depth = currentPath.length + 1;
  const link = choice.record.link_word;
  if (!Number.isInteger(link) || link < 1 || link > depth + 1) {
    throw new RangeError('Unsupported selected absolute dialogue link depth');
  }
  const visited = new Set([...visitedOffsets, node.record.offset, choice.record.offset]);
  const responseRecord = actionSuccess && choice.response ? choice.response.record : null;
  let target = [...currentPath];
  let forwardDescended = false;
  if (actionSuccess && link > depth) {
    if (!choice.response) throw new RangeError('Original forward link has no child response');
    // NE1:32a6 checks the first option-response pointer; descent returns before rewind.
    if (choice.response.choices.length && choice.response.choices[0].response) {
      target.push(choiceIndex);
      forwardDescended = true;
    }
  } else {
    while (link <= target.length + 1) {
      if (!target.length) { target = null; break; }
      target.pop();
    }
  }
  while (target?.length && !forwardDescended) {
    const current = responseAtPath(graph, target);
    if (current.choices.some(c => c.record.word0 === 0 && !visited.has(c.record.offset) && c.record.text.bytes_hex.length)) break;
    target.pop();
  }
  return {nextPath: target, visitedOffsets: visited, selectedRecord: choice.record, responseRecord};
}
