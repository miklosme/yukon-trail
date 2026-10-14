import struct,unittest
from tools.yukoncountdown import advance_countdown_day_block,finish_wharf_countdown_block,CountdownError

class CountdownTests(unittest.TestCase):
    def state(self,gate=0):
        b=bytearray([0x55]*0x400)
        for o,v in ((0x28,31),(0x2a,8),(0x30e,65535),(0x310,1),(0x334,gate)):struct.pack_into('<H',b,o,v)
        return bytes(b)
    def test_native_month_end_and_counter_wrap(self):
        after,count=advance_countdown_day_block(self.state(),1)
        self.assertEqual((struct.unpack_from('<HH',after,0x28),struct.unpack_from('<HH',after,0x30e),count),((1,9),(0,2),0))
    def test_gate_suppresses_date_but_not_decrement(self):
        before=self.state(1);self.assertEqual(advance_countdown_day_block(before,7),(before,6))
    def test_positive_branch_does_not_queue_early(self):
        before=self.state();after,count=advance_countdown_day_block(before,1)
        self.assertEqual(count,0);self.assertEqual(after[0x33a:0x33c],before[0x33a:0x33c])
    def test_completion_has_explicit_cleanup_prerequisites_and_no_date_advance(self):
        before=self.state();scene=bytearray([0x55]*128);struct.pack_into('<H',scene,4,4000);struct.pack_into('<I',scene,0x18,0x60005000);struct.pack_into('<HH',scene,0x1c,65535,65535)
        after,nextscene,manager,count=finish_wharf_countdown_block(before,bytes(scene),bytes([0x55]*128),0)
        self.assertEqual(after[0x28:0x2c],before[0x28:0x2c]);self.assertEqual(struct.unpack_from('<I',nextscene,0x18)[0],0);self.assertEqual(struct.unpack_from('<4H',manager,4),(1,400,31000,0));self.assertEqual(count,0)
        struct.pack_into('<H',scene,0x1c,4)
        with self.assertRaises(CountdownError):finish_wharf_countdown_block(before,bytes(scene),bytes(128),0)
    def test_unsupported_branch_fails(self):
        with self.assertRaises(CountdownError):advance_countdown_day_block(self.state(),32768)
