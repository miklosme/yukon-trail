import hashlib,io,tarfile,tempfile,unittest,zipfile
from pathlib import Path
from tools.prepare_emulation_trial import safe_member,frozen_guest,CONFIG

class FrozenTrialTests(unittest.TestCase):
    def test_archive_paths_and_types_fail_closed(self):
        for name in ('/absolute','../escape','./x/../../escape','C:/bad','x\\escape'):
            with self.assertRaises(ValueError):safe_member(tarfile.TarInfo(name))
        entry=tarfile.TarInfo('link');entry.type=tarfile.SYMTYPE
        with self.assertRaises(ValueError):safe_member(entry)

    def fixture(self,root,rows):
        source=root/'baseline.tar.gz'
        with tarfile.open(source,'w:gz')as archive:
            for name,data in rows:
                entry=tarfile.TarInfo(name);entry.size=len(data)
                archive.addfile(entry,io.BytesIO(data))
        return source,hashlib.sha256(source.read_bytes()).hexdigest()

    def test_frozen_copy_preserves_bytes_and_is_reproducible(self):
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary);source,sha=self.fixture(root,[('./WINDOWS/WIN.INI',b'unchanged\r\n'),('./WINDOWS/._WIN.INI',bytes.fromhex('00051607')+b'metadata')])
            first=root/'one.zip';second=root/'two.zip'
            rows,omitted,_=frozen_guest(source,first,sha);frozen_guest(source,second,sha)
            self.assertEqual(first.read_bytes(),second.read_bytes())
            self.assertEqual(len(rows),1);self.assertEqual(len(omitted),1)
            with zipfile.ZipFile(first)as archive:
                self.assertEqual(archive.read('c/WINDOWS/WIN.INI'),b'unchanged\r\n')
                self.assertEqual(archive.read('.jsdos/dosbox.conf'),CONFIG.encode('ascii'))
                self.assertIsNone(archive.testzip())
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),sha)

    def test_bad_metadata_duplicate_dos_names_and_source_hash_rejected(self):
        for rows in ([('._x',b'not AppleDouble')],[('X',b'a'),('x',b'b')]):
            with tempfile.TemporaryDirectory()as temporary:
                root=Path(temporary);source,sha=self.fixture(root,rows)
                with self.assertRaises(ValueError):frozen_guest(source,root/'out.zip',sha)
                with self.assertRaises(ValueError):frozen_guest(source,root/'other.zip','0'*64)
