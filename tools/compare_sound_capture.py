#!/usr/bin/env python3
"""Align a decoded sound with native PCM capture and report scoped differences.

Requires optional NumPy/FFmpeg. Metrics do not establish identity by themselves;
combine with original scene evidence and executable-derived decoding.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np

try:
    from .find_sound_capture import read_samples, search
except ImportError:
    from find_sound_capture import read_samples, search


def metrics(template, captured):
    if len(template) != len(captured) or not len(template):
        raise ValueError('Equal nonempty sample arrays required')
    x, y = template.astype(np.float64), captured.astype(np.float64)
    x_mean, y_mean = float(x.mean()), float(y.mean())
    x, y = x - x_mean, y - y_mean
    x_energy, y_energy = float(np.dot(x, x)), float(np.dot(y, y))
    if x_energy <= 0 or y_energy <= 0:
        raise ValueError('Silent signals cannot establish waveform agreement')
    gain = float(np.dot(x, y) / x_energy)
    residual = y - gain * x
    return {'normalized_correlation': float(np.dot(x, y) / np.sqrt(x_energy * y_energy)),
            'fitted_gain': gain, 'fitted_dc_offset': y_mean - gain * x_mean,
            'residual_rms_fraction_of_capture': float(np.sqrt(np.dot(residual, residual) / y_energy))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('template', type=Path)
    parser.add_argument('capture', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('--diagnose-clock', action='store_true',
                        help='Fit a bounded +/-0.1%% clock grid as a diagnostic, not a fidelity correction')
    args = parser.parse_args()
    x, track = read_samples(args.template), read_samples(args.capture)
    found = search(x, track)
    start = round(found['peak_seconds'] * 4000)
    y = track[start:start + len(x)]
    # Refine only the capture sample phase within one4kHz sample, without
    # stretching time or changing either sound's playback rate.
    positions = np.arange(len(x), dtype=np.float64)
    track_positions = np.arange(len(track), dtype=np.float64)
    refinement = None
    for shift in np.linspace(-1, 1, 41):
        shifted = np.interp(start + shift + positions, track_positions, track)
        measured = metrics(x, shifted)
        if refinement is None or measured['normalized_correlation'] > refinement['normalized_correlation']:
            refinement = {'fractional_sample_shift': float(shift),
                          'time_stretch': 1.0, **measured}
    thirds = []
    for index in range(3):
        low, high = index * len(x) // 3, (index + 1) * len(x) // 3
        thirds.append({'start_seconds': found['peak_seconds'] + low / 4000,
                       'end_seconds': found['peak_seconds'] + high / 4000,
                       **metrics(x[low:high], y[low:high])})
    with args.capture.open('rb') as f:
        capture_sha = hashlib.file_digest(f, 'sha256').hexdigest()
    report = {'template_sha256': hashlib.sha256(args.template.read_bytes()).hexdigest(),
              'capture_sha256': capture_sha, 'capture_path': str(args.capture),
              'numpy_version': np.__version__,
              'ffmpeg_version': subprocess.check_output(['ffmpeg', '-version'], text=True).splitlines()[0],
              'comparison_rate': 4000, 'comparison_channels': 1,
              'start_seconds': found['peak_seconds'], 'end_seconds': found['peak_seconds'] + len(x) / 4000,
              'sample_count': len(x), **metrics(x, y), 'thirds': thirds,
              'fractional_phase_refinement': refinement,
              'scope': 'Aligned resampled mono waveform comparison with fitted linear gain/DC. Residual retained; not bit-identical PCM, automatic resource identity, full mixer, or general sound validation.'}
    if args.diagnose_clock:
        best = None
        for stretch in np.linspace(0.999, 1.001, 81):
            for shift in np.linspace(-1, 1, 41):
                shifted = np.interp(start + shift + positions * stretch, track_positions, track)
                measured = metrics(x, shifted)
                if best is None or measured['normalized_correlation'] > best['normalized_correlation']:
                    best = {'fractional_sample_shift': float(shift),
                            'time_stretch': float(stretch), **measured}
        report['bounded_clock_diagnostic'] = {
            'stretch_range': [0.999, 1.001], 'stretch_steps': 81,
            'phase_range_samples': [-1, 1], 'phase_steps': 41,
            'best_fit': best,
            'scope': 'Exploratory clock/phase fit only. No decoder/playback change; residual remains unexplained.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
