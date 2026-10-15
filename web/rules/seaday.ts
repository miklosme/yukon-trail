import { advanceOneOriginalDay } from './calendar.ts'
/** Bounded original NE2:32fa. Daily date/world/journal consumers are separate. */
export interface SeaDayResult {
  stateBytes: Uint8Array
  worldBytes: Uint8Array
  seed: number
}
export interface SeaMessageResult {
  stateBytes: Uint8Array
  worldBytes: Uint8Array
  textBytes: Uint8Array
  selection: number | null
}
function signed16(value: number): number {
  return value >= 32768 ? value - 65536 : value
}
function randomStep(seed: number): [number, number] {
  const next = (Math.imul(seed, 214013) + 2531011) >>> 0
  return [next, (next >>> 16) & 32767]
}
const get = (b: Uint8Array, o: number): number => b[o] | (b[o + 1] << 8)
const put = (b: Uint8Array, o: number, v: number): void => {
  b[o] = v & 255
  b[o + 1] = (v & 65535) >>> 8
}
export function seaEventUpdate(
  stateBytes: Uint8Array,
  worldBytes: Uint8Array,
  contextBytes: Uint8Array,
  seed: number,
): SeaDayResult {
  if (
    !(stateBytes instanceof Uint8Array) ||
    stateBytes.length < 0x386 ||
    !(worldBytes instanceof Uint8Array) ||
    worldBytes.length < 0x2c ||
    !(contextBytes instanceof Uint8Array) ||
    contextBytes.length < 6 ||
    !Number.isInteger(seed) ||
    seed < 0 ||
    seed > 0xffffffff
  )
    throw new Error('Explicit original state/world/context buffers and u32 seed required')
  const state = stateBytes.slice(),
    world = worldBytes.slice()
  const ship = get(state, 0x320),
    shipIndex = (ship - 1) & 65535,
    contextWord = get(contextBytes, 4)
  let counter = get(world, 0x18),
    chance: number
  if (signed16(counter) > 2) {
    if (contextWord === 0) {
      put(world, 2, 0)
      put(world, 0x2a, 0)
    } else {
      ;[seed, chance] = randomStep(seed)
      if (signed16(((chance % 100) - 3 * shipIndex) & 65535) >= 60) {
        const status = contextWord === 1 ? 1 : 2
        put(world, 2, status)
        put(world, 0x2a, 2 * shipIndex + status)
        put(world, 4, 1)
        ;[seed, chance] = randomStep(seed)
        if (ship !== 3 && chance % 100 >= 80) {
          let percent: number
          ;[seed, percent] = randomStep(seed)
          percent = (percent % 15) + 1
          const loss = Math.trunc(signed16((signed16(get(state, 0x2fe)) * percent) & 65535) / 100)
          put(world, 8, loss)
          if (get(state, 0x334) === 0) {
            const food = (get(state, 0x2fe) - loss) & 65535
            put(state, 0x2fe, signed16(food) < 0 ? 0 : food)
          }
        } else {
          put(world, 6, 0)
          put(world, 8, 0)
        }
        put(state, 0x32e, get(state, 0x32e) + 1)
      } else {
        put(world, 2, 0)
        put(world, 0x2a, 0)
      }
      counter = 0
    }
  }
  put(world, 0x18, counter + 1)
  return { stateBytes: state, worldBytes: world, seed }
}

export function seaWeatherUpdate(
  stateBytes: Uint8Array,
  worldBytes: Uint8Array,
  contextBytes: Uint8Array,
  seed: number,
): SeaDayResult {
  if (
    !(stateBytes instanceof Uint8Array) ||
    stateBytes.length < 0x386 ||
    !(worldBytes instanceof Uint8Array) ||
    worldBytes.length < 0x2c ||
    !(contextBytes instanceof Uint8Array) ||
    contextBytes.length < 6 ||
    contextBytes[0] !== 0 ||
    contextBytes[1] !== 0 ||
    !Number.isInteger(seed) ||
    seed < 0 ||
    seed > 0xffffffff
  )
    throw new Error('Only explicit original sea context0 weather buffers and u32 seed recovered')
  const state = stateBytes.slice(),
    world = worldBytes.slice()
  put(world, 0x28, 0)
  let chance: number
  ;[seed, chance] = randomStep(seed)
  chance %= 100
  if (chance >= 75) {
    put(state, 0x32e, get(state, 0x32e) + 1)
    ;[seed, chance] = randomStep(seed)
    if (get(state, 0x320) !== 3 && chance % 100 >= 80) {
      let percent: number
      ;[seed, percent] = randomStep(seed)
      percent = (percent % 15) + 1
      const loss = Math.trunc(signed16((signed16(get(state, 0x2fe)) * percent) & 65535) / 100)
      put(world, 8, loss)
      if (get(state, 0x334) === 0) {
        const food = (get(state, 0x2fe) - loss) & 65535
        put(state, 0x2fe, signed16(food) < 0 ? 0 : food)
      }
    } else {
      put(world, 6, 0)
      put(world, 8, 0)
    }
    put(world, 0, 2)
    put(world, 0x28, 1)
  } else if (chance >= 55) {
    put(world, 0, 1)
    put(state, 0x32e, get(state, 0x32e) + 1)
  } else put(world, 0, 0)
  if (get(state, 0x334) === 0) put(state, 0x31c, get(world, 0))
  let duration: number
  ;[seed, duration] = randomStep(seed)
  duration = (duration % 4) + 3
  if (get(state, 0x334) === 0) put(state, 0x31e, duration)
  return { stateBytes: state, worldBytes: world, seed }
}

export function advanceSeaDayBeforeJournal(
  stateBytes: Uint8Array,
  worldBytes: Uint8Array,
  contextBytes: Uint8Array,
  seed: number,
): SeaDayResult {
  if (
    !(stateBytes instanceof Uint8Array) ||
    stateBytes.length < 0x386 ||
    !(worldBytes instanceof Uint8Array) ||
    worldBytes.length < 0x38 ||
    !(contextBytes instanceof Uint8Array) ||
    contextBytes.length < 6 ||
    contextBytes[0] !== 0 ||
    contextBytes[1] !== 0 ||
    !Number.isInteger(seed) ||
    seed < 0 ||
    seed > 0xffffffff
  )
    throw new Error('Only explicit original sea context0 day buffers and u32 seed recovered')
  let state: Uint8Array = stateBytes.slice(),
    world: Uint8Array = worldBytes.slice()
  for (const offset of [2, 6, 8, 10, 12]) put(world, offset, 0)
  if (get(state, 0x334) === 0) {
    const count = (get(state, 0x31e) - 1) & 65535
    put(state, 0x31e, signed16(count) < 0 ? 0 : count)
  }
  if (signed16(get(state, 0x31e)) <= 0) {
    put(world, 0, 0)
    put(world, 0x22, 0)
    ;({
      stateBytes: state,
      worldBytes: world,
      seed,
    } = seaWeatherUpdate(state, world, contextBytes, seed))
  }
  const date = advanceOneOriginalDay({
    dayWord: get(state, 0x28),
    monthWord: get(state, 0x2a),
    elapsedWord: get(state, 0x30e),
    phaseWord: get(state, 0x310),
    gate334Word: get(state, 0x334),
  })
  for (const [offset, value] of [
    [0x28, date.dayWord],
    [0x2a, date.monthWord],
    [0x30e, date.elapsedWord],
    [0x310, date.phaseWord],
  ])
    put(state, offset, value)
  if (get(state, 0x31a) === 0)
    ({
      stateBytes: state,
      worldBytes: world,
      seed,
    } = seaEventUpdate(state, world, contextBytes, seed))
  if (get(state, 0x334) === 0) {
    const count = (get(state, 0x31a) - 1) & 65535
    put(state, 0x31a, signed16(count) < 0 ? 0 : count)
  }
  if (signed16(get(state, 0x31a)) <= 0) put(world, 0x0e, 0)
  return { stateBytes: state, worldBytes: world, seed }
}

export function readSeaEventStrings(normalized: Uint8Array): Uint8Array[] {
  if (
    !(normalized instanceof Uint8Array) ||
    normalized.length < 3 ||
    normalized[0] !== 9 ||
    normalized[1] !== 0 ||
    normalized.at(-1) !== 0
  )
    throw new Error('Only selected CSTR2000 count9 recovered')
  const strings: Uint8Array[] = []
  let start = 2
  for (let i = 2; i < normalized.length; i++)
    if (normalized[i] === 0) {
      strings.push(normalized.slice(start, i))
      start = i + 1
    }
  if (strings.length !== 9) throw new Error('CSTR2000 count/extent differs')
  return strings
}
export function seaMessageUpdate(
  stateBytes: Uint8Array,
  worldBytes: Uint8Array,
  contextBytes: Uint8Array,
  textBytes: Uint8Array,
  strings: Uint8Array[],
): SeaMessageResult {
  if (
    !(stateBytes instanceof Uint8Array) ||
    stateBytes.length < 0x386 ||
    !(worldBytes instanceof Uint8Array) ||
    worldBytes.length < 0x38 ||
    !(contextBytes instanceof Uint8Array) ||
    contextBytes.length < 6 ||
    contextBytes[0] !== 0 ||
    contextBytes[1] !== 0 ||
    !(textBytes instanceof Uint8Array) ||
    !textBytes.includes(0) ||
    !Array.isArray(strings) ||
    strings.length !== 9 ||
    strings.some((s) => !(s instanceof Uint8Array) || s.includes(0))
  )
    throw new Error('Explicit selected sea0 buffers and nine CSTR2000 byte strings required')
  const world = worldBytes.slice(),
    text = textBytes.slice()
  const ship = get(stateBytes, 0x320),
    contextWord = get(contextBytes, 4),
    weatherMarker = get(world, 0x28),
    eventMarker = get(world, 0x2a)
  if (
    ![1, 2, 3].includes(ship) ||
    ![0, 1, 2].includes(contextWord) ||
    ![0, 1].includes(weatherMarker) ||
    eventMarker > 6
  )
    throw new Error('Only source-produced sea marker/ship/context domains recovered')
  let status = 0,
    selection: number | null = null
  if (eventMarker !== 0) {
    const flagIndex = eventMarker + 3
    put(world, 0x32, flagIndex)
    if (get(stateBytes, 0x19e + 2 * flagIndex) === 0) {
      selection = contextWord * 3 + ship - 1
      status = eventMarker + 33
    }
  }
  if (selection === null && weatherMarker !== 0) {
    put(world, 0x32, weatherMarker)
    if (get(stateBytes, 0x19e + 2 * weatherMarker) === 0) {
      selection = ship - 1
      status = weatherMarker + 30
    }
  }
  if (selection !== null) {
    const replacement = strings[selection]
    if (replacement.length + 1 > text.length)
      throw new Error('Original copied string exceeds explicit text capacity')
    text.set(replacement)
    text[replacement.length] = 0
  }
  put(world, 0x1c, status)
  for (const offset of [0x2c, 0x28, 0x2a, 0x2e, 0x30]) put(world, offset, 0)
  return { stateBytes: stateBytes.slice(), worldBytes: world, textBytes: text, selection }
}

export function advanceSeaDay(
  stateBytes: Uint8Array,
  worldBytes: Uint8Array,
  contextBytes: Uint8Array,
  textBytes: Uint8Array,
  strings: Uint8Array[],
  seed: number,
): SeaMessageResult & { seed: number } {
  const day = advanceSeaDayBeforeJournal(stateBytes, worldBytes, contextBytes, seed)
  const message = seaMessageUpdate(day.stateBytes, day.worldBytes, contextBytes, textBytes, strings)
  return { ...message, seed: day.seed }
}
