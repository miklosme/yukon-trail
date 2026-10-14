import unittest
from tools.yukonbmp import Frame
from tools.compare_journal_capture import compare_pixels, journal_layout


class JournalCaptureTests(unittest.TestCase):
    def test_zero_key_and_clipping_are_counted_separately(self):
        palette = bytes(3) + bytes([12, 0, 0]) + bytes(762)
        frame = Frame(3, 1, 0, 0, b'\x00\x01\x01')
        result = compare_pixels(frame, palette, (2, 1, bytes([99, 99, 99, 12, 0, 0])),
                                (0, 0), [(0, 0, 3, 1)], (0, 0, 2, 1), True)
        self.assertEqual((result['compared_pixels'], result['excluded_zero_pixels'],
                          result['excluded_clip_pixels'], result['mismatches']), (1, 1, 1, 0))

    def test_background_keeps_zero_and_unions_source_crops(self):
        # Independent six-bit DAC expectation: FF/80/04 becomes FF/82/04.
        palette = bytes([255, 128, 4]) + bytes(765)
        frame = Frame(3, 1, 0, 0, bytes(3))
        result = compare_pixels(frame, palette, (2, 1, bytes([255, 130, 4])*2),
                                (0, 0), [(0, 0, 2, 1), (1, 0, 1, 1)], (0, 0, 2, 1), False)
        self.assertEqual((result['candidate_pixels'], result['compared_pixels'],
                          result['excluded_zero_pixels'], result['mismatches']), (2, 2, 0, 0))

    def test_mismatch_details_and_invalid_bounds(self):
        frame = Frame(1, 1, 0, 0, bytes(1))
        capture = (1, 1, bytes([1, 2, 3]))
        result = compare_pixels(frame, bytes(768), capture, (0, 0), [(0, 0, 1, 1)], (0, 0, 1, 1), False)
        self.assertEqual(result['mismatches'], 1)
        self.assertEqual(result['examples'][0]['actual_rgb'], [1, 2, 3])
        for rects, clip in [([], (0, 0, 1, 1)), ([(0, 0, 2, 1)], (0, 0, 1, 1)),
                            ([(0, 0, 1, 1)], (0, 0, 2, 1))]:
            with self.assertRaises(ValueError):
                compare_pixels(frame, bytes(768), capture, (0, 0), rects, clip, False)
        with self.assertRaises(ValueError):
            journal_layout(b'not the verified executable')
        with self.assertRaises(ValueError):
            compare_pixels(frame, bytes(768), capture, (2, 2), [(0, 0, 1, 1)], (0, 0, 1, 1), False)


if __name__ == '__main__': unittest.main()
