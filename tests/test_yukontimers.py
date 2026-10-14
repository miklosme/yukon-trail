import struct,unittest
from tools.yukontimers import countdown_period,initialize_timer_table,register_timer,cancel_timer,poll_timers,TimerError

class TimerTests(unittest.TestCase):
    def test_original_countdown_periods(self):
        self.assertEqual(countdown_period(7),(7,47));self.assertEqual(countdown_period(14),(14,38));self.assertEqual(countdown_period(65535),(1,150))
    def test_original_constructor_extent(self):
        self.assertEqual(initialize_timer_table(bytes([0x55]*32)),bytes(20)+bytes([0x55]*12))
    def test_original_registration_preserves_padding_and_failure_returns_slot(self):
        table,record,index=register_timer(bytes(20),bytes([0x5a]*8),0x40005000,47,31,True)
        self.assertEqual((index,record[0],record[1],struct.unpack_from('<HI',record,2)),(0,1,0x5a,(47,48)))
        self.assertEqual(register_timer(bytes(20),bytes([0x5a]*8),0x40005000,47,31,False),(bytes(20),bytes([0x5a]*8),0))
    def test_late_poll_fires_once_and_restarts_from_fresh_clock(self):
        pointer=0x40005000;table=struct.pack('<I',pointer)+bytes(16);record=b'\1\x5a'+struct.pack('<HI',2,0);clocks=iter([1600,1632]);events=[]
        _,heap,fired=poll_timers(table,{pointer:record},lambda:next(clocks),lambda slot,t,h:events.append(slot))
        self.assertEqual((events,fired,struct.unpack_from('<I',heap[pointer],4)[0]),([0],[0],104))
    def test_callback_removal_skips_rescheduling_clock(self):
        pointer=0x40005000;table=struct.pack('<I',pointer)+bytes(16);record=b'\1\x5a'+struct.pack('<HI',2,0)
        def remove(slot,t,h):struct.pack_into('<I',t,slot*4,0)
        clocks=iter([1600]);result,_,fired=poll_timers(table,{pointer:record},lambda:next(clocks),remove)
        self.assertEqual((result,fired),(bytes(20),[0]))
    def test_one_past_constructor_cancel_is_explicitly_excluded(self):
        with self.assertRaises(TimerError):cancel_timer(bytes(20),5)
