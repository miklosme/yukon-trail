import struct
import tempfile
from pathlib import Path
import unittest
import wave

from tools.yukonsnd import SoundError, decode, integrate, write_wav
from tests.test_yukonbmp import bits, uniform


def sound_payload(text):
    text = text.replace(" ", "")
    stream = bits(text)
    chunk = struct.pack("<HBBII", 54, 3, 2, len(text), 64) + bytes(42) + stream
    return bytes.fromhex("01 81 0c 00 00 00 01 08 16 01 02 19") + bytes.fromhex("02 80 0a 00 00 00 00 00 00 00 00 80 06 00 00 00") + chunk


class SoundTests(unittest.TestCase):
    def test_independent_integration_vectors(self):
        cases = [(1, bytes([128, 129, 128])), (2, bytes([128, 129, 129]))]
        for order, expected in cases:
            self.assertEqual(integrate(bytes([128, 129, 127]), order)[0], expected)
        self.assertEqual(integrate(bytes([129, 128, 127]), 3)[0], bytes([129, 131, 133]))

    def test_byte_wrap_and_retained_state(self):
        samples, state = integrate(bytes([255, 255]), 1)
        self.assertEqual(samples, bytes([255, 126]))
        self.assertEqual(state, bytes([126, 128, 128, 128]))
        self.assertEqual(integrate(bytes([129]), 1, state)[0], bytes([127]))
        with self.assertRaises(SoundError):
            integrate(bytes(1), 5)

    def test_sequential_silence_and_metadata_retention(self):
        sound = decode(sound_payload(uniform(128)))
        self.assertEqual(sound.samples, bytes([128]) * 64)
        self.assertEqual((sound.channels, sound.sample_bits, sound.sample_rate, sound.order), (1, 8, 22050, 2))
        self.assertEqual(sound.record_metadata, bytes.fromhex("02 80 0a 00 00 00 00 00 00 00"))
        self.assertEqual(sound.chunk_metadata, bytes(42))

    def test_default_zigzag_palette_without_local_control_bits(self):
        # Type0, p=1/e=1, max255: symbol0 maps128, escaped1+0 maps127.
        text = "00 000 000" + "010" * 32
        sound = decode(sound_payload(text))
        self.assertEqual(sound.encoded_values, bytes([128, 127]) * 32)

    def test_malformed_and_unsupported_sound(self):
        payload = sound_payload(uniform(128))
        candidates = [b"", payload[:-1]]
        for offset, value in [(0, 3), (6, 2), (7, 16), (8, 11), (10, 3), (12, 3), (20, 255), (22, 1), (30, 4), (31, 1)]:
            changed = bytearray(payload)
            changed[offset] = value
            candidates.append(bytes(changed))
        for candidate in candidates:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                decode(candidate)

    def test_wav_parameters_and_unsigned_samples(self):
        sound = decode(sound_payload(uniform(128)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sound.wav"
            write_wav(sound, path)
            with wave.open(str(path), "rb") as result:
                self.assertEqual((result.getnchannels(), result.getsampwidth(), result.getframerate(), result.getnframes()), (1, 1, 22050, 64))
                self.assertEqual(result.readframes(64), bytes([128]) * 64)


if __name__ == "__main__":
    unittest.main()
