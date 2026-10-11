#!/usr/bin/env python3
"""Exploratory normalized waveform search; peaks do not confirm resource identity.

Optional NumPy and FFmpeg analysis tools; limited to ten-minute capture inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np


def read_samples(path):
    data = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-t", "601", "-ar", "4000", "-ac", "1", "-f", "f32le", "-"])
    result = np.frombuffer(data, dtype="<f4")
    if len(result) > 600 * 4000 or not len(result) or not np.isfinite(result).all():
        raise ValueError("capture exceeds ten-minute search bounds or has invalid samples")
    return result


def search(needle, track):
    if len(track) < len(needle):
        raise ValueError("capture shorter than template")
    needle = needle - needle.mean()
    norm = np.dot(needle, needle)
    if norm <= 0:
        raise ValueError("silent template")
    fft_size = 1 << (len(track) + len(needle) - 2).bit_length()
    correlation = np.fft.irfft(np.fft.rfft(track, fft_size) * np.fft.rfft(needle[::-1], fft_size), fft_size)[len(needle) - 1:len(track)]
    squares = np.concatenate(([0], np.cumsum(track.astype(np.float64) ** 2)))
    total = np.concatenate(([0], np.cumsum(track.astype(np.float64))))
    energy = squares[len(needle):] - squares[:-len(needle)] - (total[len(needle):] - total[:-len(needle)]) ** 2 / len(needle)
    score = correlation / np.sqrt(np.maximum(energy, 1e-12) * norm)
    position = int(np.argmax(score))
    return {"peak_seconds": position / 4000, "normalized_correlation": float(score[position])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("captures", type=Path, nargs="+")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    needle = read_samples(args.template)
    results = []
    for capture in args.captures:
        with capture.open("rb") as source:
            identity = hashlib.file_digest(source, "sha256").hexdigest()
        results.append({"path": str(capture), "sha256": identity, **search(needle, read_samples(capture))})
    report = {"template_sha256": hashlib.sha256(args.template.read_bytes()).hexdigest(), "numpy_version": np.__version__,
              "ffmpeg_version": subprocess.check_output(["ffmpeg", "-version"], text=True).splitlines()[0],
              "analysis_rate": 4000, "captures": results, "scope": "exploratory peaks; no match or identity confirmation"}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
