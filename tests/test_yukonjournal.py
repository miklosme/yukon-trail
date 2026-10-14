import unittest
from tools.yukonjournal import Vocabulary, JournalError, linda_entry, append_linda_entry, linda_text_from_raw_cstr505, queue_linda_continuation
from tools.yukonseattle import State, accept_linda_effects


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.vocab = Vocabulary(tuple(f'M{n} '.encode() for n in range(1, 13)),
                                b', early. ', b', later. ', b'Place. ', b'\r\n\r\n')
        self.cstr = b'\x00\x04one\0two\0three\0four\0'

    def test_fourth_partner_string_is_selected(self):
        self.assertEqual(linda_text_from_raw_cstr505(self.cstr), b'four')

    def test_explicit_date_and_existing_journal(self):
        self.assertEqual(linda_entry(self.vocab, self.cstr, 24, 8, 0, b''), b'M8 24, early. Place. four')
        self.assertEqual(append_linda_entry(self.vocab, self.cstr, 24, 8, 0, b'old'),
                         b'old\r\n\r\nM8 24, early. Place. four')

    def test_signed_phase_boundary(self):
        self.assertEqual(linda_entry(self.vocab, self.cstr, 1, 1, 5, b''), b'M1 1, early. Place. four')
        self.assertEqual(linda_entry(self.vocab, self.cstr, 1, 1, 6, b''), b'M1 1, later. Place. four')
        self.assertEqual(linda_entry(self.vocab, self.cstr, 1, 1, 65535, b''), b'M1 1, early. Place. four')

    def test_original_component_capacity_excludes_nul(self):
        # Prefix is21 bytes: 233 fits to254,234 would reach255 and is skipped.
        for length, included in [(233, True), (234, False)]:
            payload = b'\x00\x04one\0two\0three\0' + b'x' * length + b'\0'
            result = linda_entry(self.vocab, payload, 24, 8, 0, b'')
            self.assertEqual(result, b'M8 24, early. Place. ' + (b'x' * length if included else b''))

    def test_actual_seattle_scene_thirdword_does_not_change_heading(self):
        for scene in (1000,3000,4000,65535):
            self.assertEqual(linda_entry(self.vocab,self.cstr,24,8,1,b'',(200,0,scene)),b'M8 24, early. Place. four')
        for location in ((200,0,-1),(200,0,65536),(200,0),[200,0,4000]):
            with self.assertRaises(JournalError):linda_entry(self.vocab,self.cstr,24,8,1,b'',location)

    def test_unsupported_location_and_overflow_fail(self):
        with self.assertRaises(JournalError):
            linda_entry(self.vocab, self.cstr, 24, 8, 0, b'', (200, 1, 0))
        with self.assertRaises(JournalError):
            linda_entry(self.vocab, self.cstr, 24, 8, 0, b'x' * 0x2800)

    def test_malformed_inputs_fail(self):
        for payload in (b'', self.cstr[:-1], self.cstr + b'extra\0'):
            with self.assertRaises(JournalError):
                linda_text_from_raw_cstr505(payload)
        for day, month, phase in ((0, 8, 0), (24, 0, 0), (24, 8, 65536)):
            with self.assertRaises(JournalError):
                linda_entry(self.vocab, self.cstr, day, month, phase, b'')

    def test_manager_queue_writes_only_pending_and_action(self):
        self.assertEqual(queue_linda_continuation(bytes([255]) * 16),
                         bytes.fromhex('ff ff 01 00 03 00 00 00 00 00 00 00 ff ff ff ff'))
        with self.assertRaises(JournalError):
            queue_linda_continuation(bytes(11))

    def test_composed_linda_effects_keep_explicit_date_context(self):
        result = accept_linda_effects(State(350, 0, 0, 0, 0), self.vocab, self.cstr,
                                     24, 8, 0, b'old', bytes(16), (200, 0, 0))
        self.assertEqual(result.state, State(850, 0, 4, 0, 1))
        self.assertEqual(result.journal_bytes, b'old\r\n\r\nM8 24, early. Place. four')
        self.assertEqual(result.manager_bytes[2:12], bytes.fromhex('01 00 03 00 00 00 00 00 00 00'))


if __name__ == '__main__':
    unittest.main()
