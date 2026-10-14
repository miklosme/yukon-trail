import struct
import unittest

from tools.audit_bitmaps import inspect_payload


class AuditTests(unittest.TestCase):
    def test_hand_authored_solid_frame(self):
        # One constant tile with source index 72, cropped to a 2x3 frame.
        bits = '11' + '01001000' + '0'
        packed = int(bits.ljust(16, '0'), 2).to_bytes(2, 'big')
        chunk = struct.pack('<HBBII', 12, 3, 1, 11, 64) + b'\x00\x48' + packed
        payload = struct.pack('<HHHII', 1, 2, 3, 14, len(chunk)) + chunk
        result = inspect_payload(payload)
        self.assertEqual(result['status'], 'decoded')
        self.assertEqual(result['table'][0]['header'], [12, 3, 1, 11, 64])
        self.assertEqual(result['frames'][0]['width'], 2)
        self.assertEqual(result['frames'][0]['height'], 3)

    def test_rejection_retains_raw_signed_height(self):
        payload = struct.pack('<HHHII', 1, 2, 65535, 14, 0)
        result = inspect_payload(payload)
        self.assertEqual(result['status'], 'unsupported_or_invalid')
        self.assertEqual(result['table'][0]['raw_height'], 65535)
        self.assertIsNone(result['table'][0]['header'])

    def test_truncated_table_reports_explicit_failure(self):
        result = inspect_payload(b'\x02\x00')
        self.assertEqual(result['declared_frames'], 2)
        self.assertEqual(result['table'], [])
        self.assertEqual(result['status'], 'unsupported_or_invalid')


if __name__ == '__main__':
    unittest.main()
