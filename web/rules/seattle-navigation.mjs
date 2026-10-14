// Source/native oracle: docs/navigation-recovery-evidence.json.
// Client coordinates arrive unchanged from original Win16 LPARAM; OS window
// placement and actual active sprite population are external inputs, not guessed.
import {hotspotCandidate} from './scene-resources.mjs';
const down = new Set([0x201, 0x204, 0x207]);
const up = new Set([0x202, 0x205, 0x208]);
const int = (n, min, max, label) => {
  if (!Number.isInteger(n) || n < min || n > max) throw new RangeError(`${label} outside supported range`);
  return n;
};
const word = (n, label) => int(n, 0, 65535, label);
const signed16 = n => ((n + 32768) & 65535) - 32768;
export function spritePixelHit(sprite, x, y) {
  const {rectangleTLBR, width, height, stride, pixels} = sprite;
  int(x, -32768, 32767, 'Client x'); int(y, -32768, 32767, 'Client y');
  if (!Array.isArray(rectangleTLBR) || rectangleTLBR.length !== 4 || !(pixels instanceof Uint8Array))
    throw new TypeError('Explicit source rectangle and initialized pixel buffer required');
  rectangleTLBR.forEach(n => int(n, -32768, 32767, 'Sprite rectangle'));
  int(width, 1, 32767, 'Frame width'); int(height, 1, 32767, 'Frame height'); int(stride, width, 32767, 'Stride');
  // This bounded recovery excludes the original signed-word overflow cases.
  if (width * height > 32767 || stride * height > 32767 || pixels.length < stride * height)
    throw new RangeError('Sprite hit buffer outside bounded initialized frame scope');
  const [top, left, bottom, right] = rectangleTLBR;
  if (top > bottom || left > right) throw new RangeError('Reversed sprite rectangle');
  // Manager NE2:3bea includes rectangle edges, unlike the strict HSPT fallback.
  if (x < left || x > right || y < top || y > bottom) return false;
  const index = signed16((y - top) * stride + x - left);
  if (index < 0) throw new RangeError('Unrecovered negative native pixel offset');
  // Original e78a compares against frame width*height, not stride*height.
  return index < width * height && pixels[index] !== 0;
}
export function dispatchSeattleClientButton(records, {x, y, message, activationWord,
  countdownWord, managerBusyWord, sprites, sceneDeferredActionWord = 0, handler = 'common'}) {
  int(x, -32768, 32767, 'Client x'); int(y, -32768, 32767, 'Client y');
  word(message, 'Message'); word(activationWord, 'Activation'); word(countdownWord, 'Countdown');
  word(managerBusyWord, 'Manager busy'); word(sceneDeferredActionWord, 'Scene deferred action');
  if (!['common', 'ticket-office'].includes(handler)) throw new RangeError('Unsupported source message handler');
  if (!down.has(message) && !up.has(message)) throw new RangeError('Only original selected button messages supported');
  if (!Array.isArray(sprites)) throw new TypeError('Explicit sprite tail-to-previous order required');
  if (sceneDeferredActionWord) throw new RangeError('Deferred scene action flush requires separate recovery');
  const result = {transmitted: null, activation_after: activationWord, hotspot_ordinal: null,
    selected_action: null, pending_word: 0, queued_action: null, boundary_stop: null, sprite_object_id: null};
  if (activationWord) { result.activation_after = 0; return result; }
  if (managerBusyWord) return result;
  const event = down.has(message) ? 0x464 : 0x46e;
  result.transmitted = [x, y, event];
  if (event !== 0x464 || (handler === 'common' && countdownWord)) return result;
  // Caller supplies the source context list's tail→previous order; no z-sort.
  const hit = sprites.find(s => spritePixelHit(s, x, y));
  if (hit) {
    int(hit.objectId, 0, 0xffffffff, 'Sprite object id'); result.sprite_object_id = hit.objectId;
    if (hit.objectId === 0x927c || hit.objectId === 0x927d) {
      result.pending_word = 1; result.queued_action = [1, 500, 0];
    } else if (hit.objectId === 200) result.boundary_stop = 'unexecuted_sprite_action';
    return result;
  }
  const index = hotspotCandidate(records, x, y);
  if (index === null) return result;
  const record = records[index], action = [record.actionWord0, record.actionWord1, record.actionDword];
  result.hotspot_ordinal = index; result.selected_action = action;
  if ([1, 2, 3].includes(action[0])) { result.pending_word = 1; result.queued_action = action.slice(); }
  else result.boundary_stop = 'unexecuted_action';
  return result;
}
export function queuedSeattleScene(action) {
  if (!Array.isArray(action) || action.length !== 3) throw new TypeError('Original action triple required');
  word(action[0], 'Opcode'); word(action[1], 'Category'); int(action[2], 0, 0xffffffff, 'Destination');
  if (action[0] !== 1 || action[1] !== 200 || ![1000, 2000, 3000, 4000].includes(action[2]))
    throw new RangeError('Action is outside recovered Seattle scene navigation');
  return {sceneId: action[2], category: 200,
    constructor: action[2] === 3000 ? 'NE1:bf82' : 'NE2:0002'};
}
