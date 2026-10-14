import unittest
from tools.yukonsave import read_save,SaveError,SIZE,header_status

class OriginalSaveTests(unittest.TestCase):
    def fixture(self):
        # Independent fixed-field fixture, no game media. Deliberate opaque tails.
        return b'MECC\0'+b'The Yukon Trail\0'.ljust(64,b'\0')+b'0.1\0'.ljust(10,b'\0')+bytes((n*17+9)%256 for n in range(902))+b'notes\r\n\0'+bytes([0x55])*(10240-8)

    def test_unknown_state_and_journal_tail_preserved(self):
        data=self.fixture();self.assertEqual(len(data),SIZE)
        save=read_save(data);self.assertEqual(save.bytes(),data)
        self.assertEqual(save.journal_text(),b'notes\r\n')
        self.assertEqual(save.state[:2],bytes([9,26]))
        self.assertEqual(save.word(0),6665)
        self.assertEqual(save.journal[-1],0x55)

    def test_truncated_extended_other_edition_rejected(self):
        data=self.fixture()
        for bad in (data[:-1],data+b'\0',b'NOPE\0'+data[5:],data[:69]+b'9.9\0'+data[73:]):
            with self.assertRaises(SaveError):read_save(bad)

    def test_invalid_word_and_unterminated_journal(self):
        save=read_save(self.fixture())
        for offset in (-1,901,902,'0'):
            with self.assertRaises(SaveError):save.word(offset)
        save=read_save(self.fixture()[:981]+b'x'*10240)
        with self.assertRaises(SaveError):save.journal_text()

    def test_original_ignored_header_bytes_preserved(self):
        data=bytearray(self.fixture());data[4]=255;data[25]=99;data[78]=88
        self.assertEqual(header_status(bytes(data[:79])),0)
        self.assertEqual(read_save(bytes(data)).bytes(),bytes(data))

    def test_original_version_status_is_lexical_and_older_unsupported(self):
        base=self.fixture()
        for version,status in ((b'0.0',1),(b'0.10',-3),(b'0.2',-3),(b'0.1',0)):
            data=base[:69]+version.ljust(10,b'\0')+base[79:]
            self.assertEqual(header_status(data[:79]),status)
            if status:
                with self.assertRaises(SaveError):read_save(data)
