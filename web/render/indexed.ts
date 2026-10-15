// Recovered index normalization and native NE1 copy kernels, no universal alpha.
// Scene-specific key/palette/mode selection belongs to recovered scene consumers.
export interface IndexedCopyOptions {
  width: number
  height: number
  sourceStride: number
  destinationStride: number
  sourceOffset: number
  destinationOffset: number
  reverse: boolean
  excludedIndex: number | null
}
export function windowsDisplayIndices(indices: Uint8Array): Uint8Array {
  if (!(indices instanceof Uint8Array)) throw new TypeError('Indexed bytes required')
  return indices.map((i) => ((i >= 1 && i <= 9) || i >= 245 ? 120 : i))
}
export function copyIndexedRectangle(
  source: Uint8Array,
  destination: Uint8Array,
  options: IndexedCopyOptions,
): void {
  if (!(source instanceof Uint8Array) || !(destination instanceof Uint8Array)) {
    throw new TypeError('Explicit source/destination index buffers required')
  }
  if (source.buffer === destination.buffer)
    throw new RangeError('Aliased copy behavior is unsupported')
  const {
    width,
    height,
    sourceStride,
    destinationStride,
    sourceOffset,
    destinationOffset,
    reverse,
    excludedIndex,
  } = options
  for (const value of [
    width,
    height,
    sourceStride,
    destinationStride,
    sourceOffset,
    destinationOffset,
  ]) {
    if (!Number.isSafeInteger(value) || value < 0)
      throw new RangeError('Nonnegative integer geometry required')
  }
  if (
    width < 1 ||
    height < 1 ||
    sourceStride < width ||
    destinationStride < width ||
    sourceOffset + (height - 1) * sourceStride + width > source.length ||
    destinationOffset + (height - 1) * destinationStride + width > destination.length
  ) {
    throw new RangeError('Copy rectangle outside explicit buffers')
  }
  if (
    typeof reverse !== 'boolean' ||
    (excludedIndex !== null &&
      (!Number.isInteger(excludedIndex) || excludedIndex < 0 || excludedIndex > 255))
  ) {
    throw new TypeError('Explicit copy direction and excluded index/null required')
  }
  // sourceOffset denotes the leftmost source pixel even for reverse copies;
  // original reverse kernel receives a pointer to the rightmost source pixel.
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const value = source[sourceOffset + y * sourceStride + (reverse ? width - 1 - x : x)]
      if (excludedIndex === null || value !== excludedIndex) {
        destination[destinationOffset + y * destinationStride + x] = value
      }
    }
  }
}
export function rgbaFromIndices(
  indices: Uint8Array,
  rgbPalette: Uint8Array,
): Uint8ClampedArray<ArrayBuffer> {
  if (
    !(indices instanceof Uint8Array) ||
    !(rgbPalette instanceof Uint8Array) ||
    rgbPalette.length !== 768
  ) {
    throw new TypeError('Index bytes and explicit256-entry RGB palette required')
  }
  const output = new Uint8ClampedArray(indices.length * 4)
  for (let i = 0; i < indices.length; i++) {
    const index = indices[i] * 3
    for (let channel = 0; channel < 3; channel++) {
      const value = rgbPalette[index + channel]
      output[i * 4 + channel] = ((value >> 2) << 2) | (value >> 6)
    }
    output[i * 4 + 3] = 255
  }
  return output
}
