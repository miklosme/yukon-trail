import unittest
import struct
from tools.yukoninitial import original_random_step, reset_original_state, InitialStateError

class InitialTests(unittest.TestCase):
    def test_independent_small_random_steps(self):
        # Hand arithmetic: seed*n +2531011, upperword masked7fff.
        self.assertEqual(original_random_step(0),(2531011,38))
        self.assertEqual(original_random_step(1),(2745024,41))
        self.assertEqual(original_random_step(2),(2959037,45))
        self.assertEqual(original_random_step(0xffffffff),(2316998,35))

    def test_selected_reset_defaults_and_untouched_bytes(self):
        before=bytes([0x55]*0x400)
        after=reset_original_state(before,41)
        selected={0x28:23,0x2a:8,0x30e:1,0x310:1,0x312:65535,0x220:0,0x2ac:0,0x2b2:0,0x2fa:350,0x2fc:0,0x306:0,0x318:0,0x334:0,0x344:0,0x314:9,0x316:12,0x384:0}
        for offset,value in selected.items():self.assertEqual(struct.unpack_from('<H',after,offset)[0],value)
        self.assertEqual((after[0],after[0x14]),(0,0))
        self.assertEqual(after[0x34:0x36],b'UU')
        self.assertEqual(after[1:0x14],before[1:0x14])
        self.assertEqual(after[0x386:],before[0x386:])
        self.assertEqual(before,bytes([0x55]*0x400))

    def test_explicit_inputs_required(self):
        for seed in (-1,0x100000000):
            with self.assertRaises(InitialStateError):original_random_step(seed)
        for previous,random_word in ((b'',1),(bytes(0x386),32768),(bytes(0x386),-1)):
            with self.assertRaises(InitialStateError):reset_original_state(previous,random_word)
