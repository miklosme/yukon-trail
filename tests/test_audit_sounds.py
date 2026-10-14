import hashlib
import struct
import unittest
from tools.audit_sounds import inspect_payload
from tests.test_yukonsnd import sound_payload
from tests.test_yukonbmp import uniform

class SoundAuditTests(unittest.TestCase):
    def test_source_count_and_independent_silence_pcm_identity(self):
        row=inspect_payload(sound_payload(uniform(128)))
        self.assertEqual((row['header_size'],row['flags'],row['checkpoint_count']),(54,2,5))
        self.assertEqual(row['status'],'decoded')
        self.assertEqual(row['pcm_sha256'],hashlib.sha256(bytes([128])*64).hexdigest())
        self.assertEqual((row['consumed_bits'],row['terminal_unused_bits']),(11,5))

    def test_unindexed_packed_bytes_are_not_a_count(self):
        source=sound_payload(uniform(128))
        raw=source[:28]+struct.pack('<HBBII',12,3,0,11,64)+source[82:]
        row=inspect_payload(raw)
        self.assertEqual((row['header_size'],row['flags'],row['checkpoint_count']),(12,0,None))
        self.assertEqual(row['status'],'decoded')

    def test_rejected_variant_keeps_diagnostic_fields(self):
        raw=bytearray(sound_payload(uniform(128)));raw[8]=11
        row=inspect_payload(bytes(raw))
        self.assertEqual(row['status'],'unsupported_or_invalid')
        self.assertEqual(row['rate_code'],11)
        self.assertIn('rate-code22',row['reason'])
