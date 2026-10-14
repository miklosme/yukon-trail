import struct,unittest
from tools.yukonseaday import sea_event_update,SeaDayError

class SeaEventTests(unittest.TestCase):
    def inputs(self,counter=3,ship=1,context_word=1,food=2400,gate=0):
        state=bytearray([0x55]*0x400);world=bytearray([0x55]*0x38);context=bytearray([0x55]*6)
        for o,v in ((0x320,ship),(0x2fe,food),(0x334,gate),(0x32e,65535)):struct.pack_into('<H',state,o,v)
        struct.pack_into('<H',world,0x18,counter);struct.pack_into('<H',context,4,context_word)
        return bytes(state),bytes(world),bytes(context)
    def word(self,b,o):return struct.unpack_from('<H',b,o)[0]
    def test_zero_context_skips_reset_and_rng(self):
        state,world,seed=sea_event_update(*self.inputs(context_word=0),10)
        self.assertEqual(self.word(world,0x18),4);self.assertEqual(self.word(world,2),0);self.assertEqual(self.word(world,0x2a),0);self.assertEqual(seed,10)
    def test_signed_counter_wrap_preserves_other_words(self):
        before,world,context=self.inputs(counter=65535)
        state,after,seed=sea_event_update(before,world,context,10)
        expected=bytearray(world);struct.pack_into('<H',expected,0x18,0)
        self.assertEqual(state,before);self.assertEqual(after,expected);self.assertEqual(seed,10)
    def test_original_loss_branch_and_ungated_event_counter(self):
        # Native threshold fixture seed10 yields event and3% loss; actual
        # 32fa/food instructions independently match every byte in the oracle.
        for gate,food in ((0,2328),(1,2400)):
            state,world,_=sea_event_update(*self.inputs(gate=gate),10)
            self.assertEqual(self.word(world,8),72);self.assertEqual(self.word(state,0x2fe),food);self.assertEqual(self.word(state,0x32e),0)
    def test_original_low_word_product_wrap(self):
        state,world,_=sea_event_update(*self.inputs(food=32767),10)
        self.assertEqual(self.word(world,8),327);self.assertEqual(self.word(state,0x2fe),32440)
    def test_ship_three_uses_second_rng_but_no_loss(self):
        state,world,seed=sea_event_update(*self.inputs(ship=3),10)
        self.assertEqual(self.word(world,8),0);self.assertEqual(self.word(state,0x2fe),2400);self.assertNotEqual(seed,10)
    def test_no_context_defaults(self):
        with self.assertRaises(SeaDayError):sea_event_update(bytes(0x400),bytes(0x38),b'',0)

class SeaDayCompositionTests(unittest.TestCase):
    inputs=SeaEventTests.inputs
    word=SeaEventTests.word
    def test_sea_weather_original_calm_duration(self):
        from tools.yukonseaday import sea_weather_update
        state,world,context=self.inputs()
        context=struct.pack('<3H',0,0x5555,1)
        after,weather,seed=sea_weather_update(state,world,context,0)
        self.assertEqual(self.word(weather,0),0);self.assertEqual(self.word(weather,0x28),0)
        self.assertEqual(self.word(after,0x31c),0);self.assertEqual(self.word(after,0x31e),6)
        self.assertEqual(self.word(after,0x32e),65535)
    def test_original_month_boundary_before_journal(self):
        from tools.yukonseaday import advance_sea_day_before_journal
        state,world,_=self.inputs();state=bytearray(state)
        for o,v in ((0x28,31),(0x2a,8),(0x30e,65535),(0x310,1),(0x31e,2),(0x31a,1)):struct.pack_into('<H',state,o,v)
        after,result,seed=advance_sea_day_before_journal(bytes(state),world,struct.pack('<3H',0,0x5555,1),10)
        self.assertEqual([self.word(after,o)for o in (0x28,0x2a,0x30e,0x310,0x31e,0x31a)],[1,9,0,2,1,0])
        self.assertEqual(self.word(result,0x0e),0);self.assertEqual(seed,10)
    def test_actual_strings_and_marker_fallback_preserve_seen_flags(self):
        import json
        from pathlib import Path
        from tools.yukonseaday import sea_message_update,read_sea_event_strings
        r=json.loads(Path('docs/seamessage-recovery-evidence.json').read_text())
        strings=read_sea_event_strings(b'\x09\0'+b''.join(bytes.fromhex(s)+b'\0'for s in r['resource']['strings_hex']))
        state,world,_=self.inputs();state=bytearray(state);world=bytearray(world)
        for o,v in ((0x320,2),(0x1a0,0),(0x1a8,1)):struct.pack_into('<H',state,o,v)
        for o,v in ((0x28,1),(0x2a,2)):struct.pack_into('<H',world,o,v)
        before=bytes(state);text=b'old\0'+bytes([0x55]*251)
        after,result,out,selected=sea_message_update(before,bytes(world),struct.pack('<3H',0,0,1),text,strings)
        self.assertEqual(after,before);self.assertEqual(selected,1);self.assertEqual(out.split(b'\0')[0],strings[1])
        self.assertEqual(self.word(result,0x32),1);self.assertEqual(self.word(result,0x1c),31)
        self.assertTrue(all(self.word(result,o)==0 for o in (0x28,0x2a,0x2c,0x2e,0x30)))
    def test_nonsea_weather_and_corrupt_message_domains_fail(self):
        from tools.yukonseaday import sea_weather_update,sea_message_update
        state,world,_=self.inputs()
        with self.assertRaises(SeaDayError):sea_weather_update(state,world,struct.pack('<3H',1,0,1),0)
        with self.assertRaises(SeaDayError):sea_message_update(state,world,struct.pack('<3H',0,0,9),b'\0',tuple(b'x'for _ in range(9)))
