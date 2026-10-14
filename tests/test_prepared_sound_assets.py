import hashlib
import json
import tempfile
import unittest
import wave
from pathlib import Path
from tools.verify_prepared_sound_assets import verify

class PreparedSoundTests(unittest.TestCase):
    def fixture(self,directory,rate=22050):
        # Independent exactunsigned8bit PCM fixture; no decoder used here.
        pcm=bytes([0,128,255]);path=directory/'PSND-1.wav'
        with wave.open(str(path),'wb') as sound:
            sound.setnchannels(1);sound.setsampwidth(1);sound.setframerate(rate);sound.writeframes(pcm)
        proof={'executable_sha256':'exe','archive_sha256':'archive','sounds':{'PSND:1':{'raw_sha256':'raw','sample_bytes':3,'native_pcm_sha256':hashlib.sha256(pcm).hexdigest()}}}
        manifest={'executable_sha256':'exe','archive_sha256':'archive','sounds':{'PSND:1':{'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'raw_sha256':'raw'}}}
        (directory/'manifest.json').write_text(json.dumps(manifest));return proof

    def test_actual_wav_params_and_independent_pcm_oracle(self):
        with tempfile.TemporaryDirectory() as value:
            directory=Path(value);proof=self.fixture(directory)
            self.assertEqual(verify(directory,proof)['sound_count'],1)
            proof['sounds']['PSND:1']['native_pcm_sha256']=hashlib.sha256(bytes([128]*3)).hexdigest()
            with self.assertRaises(ValueError):verify(directory,proof)

    def test_wrong_rate_fails_even_with_correct_file_and_pcm_hashes(self):
        with tempfile.TemporaryDirectory() as value:
            directory=Path(value);proof=self.fixture(directory,11025)
            with self.assertRaises(ValueError):verify(directory,proof)
