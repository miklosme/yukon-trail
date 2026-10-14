import struct
import unittest
from tools.yukonsprite import SpriteError, read_sprite, read_cel_offsets, read_animation, read_hotspots, hotspot_candidate, completed_sequence_anchor

class SpriteParserTests(unittest.TestCase):
    def test_signed_fields_and_unknown_header_preserved(self):
        payload=bytes.fromhex('90019001feff5201')+bytes(8)+bytes.fromhex('ffffffff')+bytes(10)+bytes.fromhex('ffffffff0100')+bytes.fromhex('01000500640000000000')
        sprite=read_sprite(payload)
        self.assertEqual((sprite.bitmap_id,sprite.animation_id,sprite.anchor_x,sprite.anchor_y),(400,400,-2,338))
        self.assertEqual((sprite.initial_sequence,sprite.click_sequence),(-1,-1))
        self.assertEqual(sprite.raw_header,payload[:38])
        self.assertEqual(sprite.schedules,((5,100,0,0),))

    def test_sprite_count_and_truncation_fail(self):
        for payload in (b'',bytes(37),bytes(39),bytes(36)+b'\1\0'):
            with self.assertRaises(SpriteError):read_sprite(payload)

    def test_cel_offsets_signed_and_exact_length(self):
        self.assertEqual(read_cel_offsets(bytes.fromhex('02000500f9ff0a00f5ff')),((5,-7),(10,-11)))
        for payload in (b'',b'\1\0',bytes.fromhex('01000500f9ff00')):
            with self.assertRaises(SpriteError):read_cel_offsets(payload)

    def test_animation_range_and_length_fail(self):
        # One descriptor references one step that is absent from a zero-step table.
        payload=struct.pack('<HHhHHH',1,0,-1,10,1,0)
        with self.assertRaises(SpriteError):read_animation(payload)
        with self.assertRaises(SpriteError):read_animation(b'\1\0')
        with self.assertRaises(SpriteError):read_animation(b'\0\0\0\0\0')

    def test_unknown_motion_is_not_silently_applied(self):
        header=struct.pack('<HHhHHH',1,0,-1,10,1,1)
        animation=read_animation(header+struct.pack('<HhhHHH',0,4,-10,9,0,0))
        sprite=read_sprite(bytes(36)+b'\0\0')
        with self.assertRaises(SpriteError):completed_sequence_anchor(sprite,animation,0)

    def test_hotspot_edges_first_match_and_sentinel(self):
        payload=struct.pack('<H',3)+struct.pack('<hhhhHHI',10,30,20,40,1,200,1000)+struct.pack('<hhhhHHI',15,35,25,45,2,201,1001)+bytes(16)
        records=read_hotspots(payload)
        self.assertEqual(hotspot_candidate(records,20,30),0)
        for point in ((10,20),(10,30),(30,20),(20,20)):
            self.assertIsNone(hotspot_candidate(records,*point))
        self.assertEqual(hotspot_candidate(records,32,30),1)
        self.assertEqual(records[0].action_dword,1000)

    def test_hotspot_malformed_tables_fail(self):
        for payload in (b'',b'\1\0',struct.pack('<HhhhhHHI',1,10,30,20,40,1,200,1000)):
            with self.assertRaises(SpriteError):read_hotspots(payload)

    def test_hotspot_point_domain_is_explicit(self):
        records=read_hotspots(b'\1\0'+bytes(16))
        for point in ((32768,0),(0,-32769),(1.5,0)):
            with self.assertRaises(SpriteError):hotspot_candidate(records,*point)

if __name__=='__main__':unittest.main()
