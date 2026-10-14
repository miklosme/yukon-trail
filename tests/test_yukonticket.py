import struct
import unittest
from tools.yukonticket import purchase_ticket,queue_boarding,select_clerk_tree,selected_boarding_choice,TicketError

class TicketTests(unittest.TestCase):
    def state(self,cash,ticket=0,gate=0):
        b=bytearray([0x55]*0x400)
        for o,v in [(0x2fa,cash),(0x2fc,0),(0x304,ticket),(0x334,gate)]:struct.pack_into('<H',b,o,v)
        return bytes(b)
    def test_observed_al_ki_fare(self):
        after,result=purchase_ticket(self.state(422),(250,254,80,0))
        self.assertEqual((struct.unpack_from('<H',after,0x2fa)[0],struct.unpack_from('<H',after,0x304)[0],struct.unpack_from('<HH',after,0x320),result),(342,1,(3,9000),1))
    def test_source_yosemite_fare_and_failure_return_ignored(self):
        after,result=purchase_ticket(self.state(20),(250,252,60,0))
        self.assertEqual((struct.unpack_from('<HH',after,0x2fa),struct.unpack_from('<H',after,0x304)[0],struct.unpack_from('<HH',after,0x320),result),((20,0),1,(2,5000),1))
    def test_gate_preserves_full_original_state(self):
        before=self.state(422,gate=1)
        self.assertEqual(purchase_ticket(before,(250,254,80,0)),(before,1))
    def test_source_clerk_and_ship_conditions(self):
        self.assertEqual([select_clerk_tree(p,s) for p,s in [(65535,0),(4,0),(4,3)]],[3500,3550,3570])
        self.assertTrue(selected_boarding_choice(3,0));self.assertTrue(selected_boarding_choice(2,1));self.assertTrue(selected_boarding_choice(1,2));self.assertFalse(selected_boarding_choice(0,0))
    def test_immediate_and_delayed_queues_preserve_date(self):
        before=self.state(342,ticket=1)
        for delay,packet in [(0,(1,400,31000,0)),(7,(3,0,0,0)),(14,(3,0,0,0))]:
            after,parent,manager,result=queue_boarding(before,bytes([0x55]*128),bytes([0x55]*128),(320,delay,0,0))
            self.assertEqual(after[0x28:0x2c],before[0x28:0x2c]);self.assertEqual(struct.unpack_from('<H',after,0x304)[0],0)
            self.assertEqual(struct.unpack_from('<4H',parent,0x10),(320,delay,0,0));self.assertEqual(struct.unpack_from('<4H',manager,4),packet);self.assertEqual(result,1)
    def test_unsupported_fares_or_waits_fail(self):
        with self.assertRaises(TicketError):purchase_ticket(self.state(422),(250,254,81,0))
        with self.assertRaises(TicketError):queue_boarding(self.state(342),bytes(128),bytes(128),(320,1,0,0))
