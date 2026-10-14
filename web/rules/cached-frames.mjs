// Source/native full-buffer proof: docs/cached-frame-recovery-evidence.json.
export function cachedFrameView(record, bytes) {
  if (record?.format !== 'original-windows-cache-indices-v1' || !(bytes instanceof Uint8Array))
    throw new TypeError('Explicit normalized cached-frame record and bytes required');
  const {width, height, stride, allocated_height: allocatedHeight, allocation_bytes: allocationBytes} = record;
  for (const n of [width, height]) if (!Number.isInteger(n) || n <= 0 || n >= 32768)
    throw new RangeError('Only positive bounded native frame dimensions supported');
  if (stride !== ((width + 7) & ~7) || allocatedHeight !== ((height + 7) & ~7) ||
      allocationBytes !== stride * allocatedHeight || bytes.length !== allocationBytes)
    throw new RangeError('Cached frame stride/allocation length differs');
  return {width, height, stride, allocatedHeight, pixels: bytes};
}
// Pixel buffers must already have been checked against import provenance hashes.
// Missing or lossless-visible-only buffers throw; no padding default is generated.
export function cachedFrameProvider(metadata, checkedBuffers) {
  if (metadata?.schema !== 'selected-cached-frame-buffers-v1' || !(checkedBuffers instanceof Map))
    throw new TypeError('Source cache metadata and checked buffer map required');
  return (bitmapId, frame) => {
    const record = metadata.frames[`${bitmapId}:${frame}`];
    if (!record) throw new RangeError('Frame outside recovered cached-frame import');
    const bytes = checkedBuffers.get(record.pixels_file);
    return cachedFrameView(record, bytes);
  };
}
