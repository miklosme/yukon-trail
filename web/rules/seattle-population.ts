// Original constructor oracle: docs/seattle-population-recovery-evidence.json.
import {SOURCE_EXE_SHA256, frameRectangle, type RectangleTLBR} from './scene-resources.ts';
import type {SpriteHitContext} from './seattle-navigation.ts';
/** tools/prepare_seattle_population.py output (schema seattle-initial-population-source-v1). */
export interface SeattlePopulationSource {
  schema: string;
  executable_sha256: string;
  archive_sha256: string;
  animations: Record<string, {sequences: number[][]; steps: number[][]; cel_offsets_xy: number[][]}>;
  bitmaps: Record<string, {frame_sizes_wh: number[][]}>;
  sprites: Record<string, {
    bitmap_id: number;
    animation_id: number;
    anchor_xy: number[];
    initial_sequence: number;
    raw_header_words: number[];
    schedules: number[][];
  }>;
  /** Controller records per scene: [kind, sprite id, flags, cond kind/value ×3]. */
  scenes: Record<string, {records: number[][]}>;
}
export interface ActorPose {
  object_id: number;
  sprite_id: number | null;
  bitmap_id: number;
  frame: number;
  rectangle_tlbr: RectangleTLBR;
  anchor_yx: [number, number];
  visible_word: number;
  flip_byte: number;
  sequence_word: number;
  animation_deadline: number;
  schedule_deadline: number | null;
}
export interface InitialSeattlePopulation {
  controller_record_words: number[][];
  context_head_to_next: ActorPose[];
}
export interface InitialPopulationInputs {
  sceneId: number;
  partnerWord: number;
  property320Word: number;
  downtownVisitWord: number;
  regionArrivalWord: number;
  clockMs: number;
  mmclockMs: number;
}
interface PoseRequest {
  spriteId: number | null;
  bitmapId: number;
  animationId: number;
  anchorXY: readonly number[];
  sequence: number;
  scheduleInterval: number | null;
  zeroInitialOffset: boolean;
}
const int = (n: number, max: number, label: string): number => {
  if (!Number.isInteger(n) || n < 0 || n > max) throw new RangeError(`${label} outside supported range`);
  return n;
};
const signed16 = (n: number): number => ((n + 32768) & 65535) - 32768;
function predicate(kind: number, value: number, visit: number): boolean {
  if (kind === 0) return true;
  if (kind === 3 && [1, 2].includes(value)) return value === 2;
  if (kind === 8 && [1, 2].includes(value)) return value === 2;
  if (kind === 28 && [1, 2].includes(value)) return value === (visit === 0 ? 1 : 2);
  throw new RangeError(`Unrecovered initial controller condition ${kind}/${value}`);
}
function pose(source: SeattlePopulationSource, {spriteId, bitmapId, animationId, anchorXY, sequence, scheduleInterval, zeroInitialOffset}: PoseRequest, clock: number, mmclock: number): ActorPose {
  const animation = source.animations[animationId], bitmap = source.bitmaps[bitmapId];
  if (!animation || !bitmap) throw new RangeError('Required source animation/bitmap metadata absent');
  const descriptor = animation.sequences[sequence];
  if (!descriptor || descriptor[3] === 0) throw new RangeError('Unsupported empty initial sequence');
  const step = animation.steps[descriptor[0]];
  if (!step || step[3] !== 0) throw new RangeError('Unsupported initial animation step');
  const [frame, dx, dy, , override, toggle] = step;
  const initialOffset = zeroInitialOffset ? [0, 0] : animation.cel_offsets_xy[0];
  // Original only invokes the ACEL frame setter when the frame differs from zero.
  const offset = frame === 0 ? initialOffset : animation.cel_offsets_xy[frame];
  const size = bitmap.frame_sizes_wh[frame];
  if (!offset || !size) throw new RangeError('Initial frame outside source tables');
  const flip = toggle ? 1 : 0;
  const xy = [signed16(anchorXY[0] + (flip ? -dx : dx)), signed16(anchorXY[1] + dy)];
  return {object_id: spriteId === null ? bitmapId : 200, sprite_id: spriteId, bitmap_id: bitmapId, frame,
    rectangle_tlbr: frameRectangle(xy, offset, size), anchor_yx: [xy[1], xy[0]], visible_word: 1,
    flip_byte: flip, sequence_word: sequence, animation_deadline: (Math.floor(clock / 17) + (override || descriptor[2])) >>> 0,
    schedule_deadline: scheduleInterval === null ? null : (Math.floor(mmclock / 16) + scheduleInterval) >>> 0};
}
export function initialSeattlePopulation(source: SeattlePopulationSource, {sceneId, partnerWord, property320Word, downtownVisitWord,
  regionArrivalWord, clockMs, mmclockMs}: InitialPopulationInputs): InitialSeattlePopulation {
  if (source?.schema !== 'seattle-initial-population-source-v1' || source.executable_sha256 !== SOURCE_EXE_SHA256)
    throw new TypeError('Verified initial population source metadata required');
  if (![1000, 2000, 3000, 4000].includes(sceneId)) throw new RangeError('Unsupported Seattle scene');
  if (partnerWord !== 65535 || property320Word !== 0) throw new RangeError('Only explicit unpartnered fresh-condition state supported');
  int(downtownVisitWord, 1, 'Downtown pre-entry visit'); int(regionArrivalWord, 1, 'Seattle pre-entry arrival');
  int(clockMs, 0xffffffff, 'GetTickCount'); int(mmclockMs, 0xffffffff, 'TimeGetTime');
  const records = source.scenes[sceneId]?.records;
  if (!records) throw new RangeError('Source controller records absent');
  const admitted = records.filter(r => {
    for (let p = 3; p < 9; p += 2) if (!predicate(r[p], r[p + 1], downtownVisitWord)) return false;
    return true;
  });
  const contexts = admitted.map(record => {
    if (record[0] !== 3 || record[2] !== 0) throw new RangeError('Unsupported controller actor kind/flags');
    const id = record[1], s = source.sprites[id];
    if (!s || s.initial_sequence !== -1 || s.raw_header_words[4] !== 0 || !s.schedules.length)
      throw new RangeError('Unsupported SPRT initial callback/sequence');
    return pose(source, {spriteId: id, bitmapId: s.bitmap_id, animationId: s.animation_id,
      anchorXY: s.anchor_xy, sequence: s.schedules[0][0], scheduleInterval: s.schedules[0][1], zeroInitialOffset: false}, clockMs, mmclockMs);
  });
  const arrivals: [number, [number, number], number][] =
    [[37500, [110, 100], regionArrivalWord === 0 ? 1 : 0], [37501, [80, 122], 0]];
  for (const [id, anchor, sequence] of arrivals)
    contexts.push(pose(source, {spriteId: null, bitmapId: id, animationId: id, anchorXY: anchor,
      sequence, scheduleInterval: null, zeroInitialOffset: true}, clockMs, mmclockMs));
  return {controller_record_words: admitted.map(r => r.slice()), context_head_to_next: contexts};
}
export type InitializedFrameProvider = (bitmapId: number, frame: number) =>
  {width: number; height: number; stride: number; pixels: Uint8Array};
// Caller must supply the actual initialized native-layout indexed frame buffer,
// including its stride/padding. This helper does not invent padding pixels.
export function populationHitContexts(population: InitialSeattlePopulation, initializedFrame: InitializedFrameProvider): SpriteHitContext[] {
  if (typeof initializedFrame !== 'function') throw new TypeError('Initialized indexed-frame provider required');
  return population.context_head_to_next.slice().reverse().map(p => {
    const {width, height, stride, pixels} = initializedFrame(p.bitmap_id, p.frame);
    if (!(pixels instanceof Uint8Array)) throw new TypeError('Actual indexed source frame required');
    return {objectId: p.object_id, rectangleTLBR: p.rectangle_tlbr.slice(), width, height, stride, pixels};
  });
}
