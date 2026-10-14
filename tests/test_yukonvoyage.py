import json,struct,unittest
from pathlib import Path
from tools.yukonvoyage import read_sea_map,advance_sea_waypoint,VoyageError

class VoyageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=tuple(tuple(r) for r in json.loads((Path(__file__).resolve().parents[1]/'docs/voyage-waypoint-recovery-evidence.json').read_text())['resource']['records'])
    def context(self,index=0,partial=24,speed=18,destination=9000):
        state=bytearray([0x55]*0x400);scene=bytearray([0x55]*0xa6)
        struct.pack_into('<H',state,0x334,0);struct.pack_into('<H',state,0x322,destination)
        for o,v in ((0x88,index),(0x8c,partial),(0x96,speed)):struct.pack_into('<H',scene,o,v)
        return bytes(state),bytes(scene),bytes([0x55]*128)
    def test_source_map_extent_and_unknown_event_rejection(self):
        data=struct.pack('<H',45)+b''.join(struct.pack('<3H',*r) for r in self.rows)
        self.assertEqual(read_sea_map(data),self.rows)
        for bad in (data[:-1],data+b'\0\0',struct.pack('<H',44)+data[2:]):
            with self.assertRaises(VoyageError):read_sea_map(bad)
        bad=bytearray(data);struct.pack_into('<H',bad,6,999)
        with self.assertRaises(VoyageError):read_sea_map(bad)
    def test_one_row_per_call_even_when_remainder_exceeds_threshold(self):
        before,scene,manager=self.context(partial=100,speed=18)
        after,nextscene,_,_,_,_=advance_sea_waypoint(before,scene,manager,self.rows,1,2)
        self.assertEqual((struct.unpack_from('<H',nextscene,0x88)[0],struct.unpack_from('<H',nextscene,0x8c)[0]),(1,93));self.assertEqual(after[0x28:0x2c],before[0x28:0x2c])
    def test_actual_final_row_queues_selected_destination_and_resets_progress(self):
        index=next(i for i,r in enumerate(self.rows) if r[2]==2);before,scene,manager=self.context(index=index)
        after,nextscene,nextmanager,seed,opens,audio=advance_sea_waypoint(before,scene,manager,self.rows,1,2)
        self.assertEqual(struct.unpack_from('<4H',nextmanager,4),(1,200,9000,0));self.assertEqual(struct.unpack_from('<H',nextscene,0x88)[0],0);self.assertEqual(struct.unpack_from('<H',nextscene,0x8c)[0],0);self.assertEqual((seed,opens,audio),(1,[],[]))
    def test_out_of_source_range_fails(self):
        before,scene,manager=self.context(index=45)
        with self.assertRaises(VoyageError):advance_sea_waypoint(before,scene,manager,self.rows,1,2)
