import unittest

from tools.yukontransform import TransformError, transform


class TransformTests(unittest.TestCase):
    def test_word_dword_prefix_preserves_trailing_data(self):
        source = bytes.fromhex('123489abcdef') + b'text'
        self.assertEqual(transform(source, (-2, -3, 0)), bytes.fromhex('3412efcdab89') + b'text')
        self.assertEqual(source, bytes.fromhex('123489abcdef') + b'text')

    def test_counted_records(self):
        self.assertEqual(transform(bytes.fromhex('00020123abcd') + b'end', (-4, -2, -5, 0)),
                         bytes.fromhex('02002301cdab') + b'end')

    def test_zero_count_still_visits_first_body_if_data_remains(self):
        self.assertEqual(transform(bytes.fromhex('0000aabbccdd'), (-4, -2, -5, 0)),
                         bytes.fromhex('0000bbaaccdd'))

    def test_count_at_payload_end_returns_without_body(self):
        self.assertEqual(transform(bytes.fromhex('0000'), (-4, -2, -5, 0)), b'\0\0')

    def test_byte_and_256_byte_skips(self):
        source = b'X\x01\x02' + b'z'*256 + b'\x03\x04tail'
        self.assertEqual(transform(source, (-1, -2, -6, -2, 0)),
                         b'X\x02\x01' + b'z'*256 + b'\x04\x03tail')

    def test_signed_skip(self):
        self.assertEqual(transform(bytes.fromhex('12345678'), (-1, -8, -1, -2, 0)),
                         bytes.fromhex('34125678'))

    def test_whole_words(self):
        self.assertEqual(transform(bytes.fromhex('0123456789ab'), (-7, 0)),
                         bytes.fromhex('23016745ab89'))

    def test_missing_tag_and_noop(self):
        for payload in (b'', b'abc'):
            self.assertEqual(transform(payload, None), payload)
            self.assertEqual(transform(payload, (0,)), payload)

    def test_bounds_and_unsupported_patterns(self):
        for payload, opcodes in [(b'x', (-2, 0)), (b'xyz', (-7, 0)),
                                 (b'', (-7, 0)), (b'x', (-6, 0)),
                                 (b'xxxx', (-4, -4, 0)), (b'x', (-5, 0)),
                                 (b'x', (-9, 0)), (b'x', (-2,))]:
            with self.subTest(opcodes=opcodes), self.assertRaises(TransformError):
                transform(payload, opcodes)
