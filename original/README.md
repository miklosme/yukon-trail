# Local source material

The source image is expected at `iso/YUKONCD.ISO` relative to this directory. Keep supplied media unchanged. This directory’s README is versioned; the actual media and extracted contents are ignored by Git.

- `iso/`: original image, accompanying tracks, and download metadata.
- `extracted/windows/`: selected or complete ISO9660 extraction.
- `extracted/mac/`: separate HFS extraction preserving resource forks and metadata.

Do not mix full-game files with demo files, or Mac resources with Windows resources. Record edition/source hashes when introducing another image. Essential provenance belongs in [the versioned source manifest](../docs/source-manifest.json), not solely in local download metadata.

See [the workflow](../docs/WORKFLOW.md) for extraction commands and [the findings](../docs/FINDINGS.md) for what has actually been inspected. Converted resources belong in `generated/` at the repository root; analysis databases and emulator state belong in `local/`.
