import unittest
from tools.yukonbmp import Frame
from tools.compare_background_capture import compare


class BackgroundCaptureTests(unittest.TestCase):
    def test_cropped_source_and_overlapping_rectangles(self):
        palette = b'\xff\x80\x04' + bytes(765)
        # Capture shows only left two pixels; third source pixel is clipped.
        frame = Frame(3, 1, 0, 0, b'\x00\x00\x01')
        result = compare(frame, palette, (2, 1, b'\xff\x82\x04'*2), (0, 0),
                         [(0, 0, 2, 1), (1, 0, 1, 1)])
        self.assertEqual(result['compared_pixels'], 2)
        self.assertEqual(result['mismatches'], 0)

    def test_exact_difference_and_bounds(self):
        frame = Frame(1, 1, 0, 0, b'\x00')
        self.assertEqual(compare(frame, bytes(768), (1, 1, b'\x00\x00\x01'),
                                 (0, 0), [(0, 0, 1, 1)])['mismatches'], 1)
        for rectangles in ([], [(0, 0, 2, 1)], [(-1, 0, 1, 1)]):
            with self.assertRaises(ValueError):
                compare(frame, bytes(768), (1, 1, bytes(3)), (0, 0), rectangles)
