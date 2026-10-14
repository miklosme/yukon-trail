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
    chunk = struct.pack("<HBBII", 54, 3, 2, len(text), 64) + struct.pack("<H",5) + bytes(40) + stream
    return bytes.fromhex("01 81 0c 00 00 00 01 08 16 01 02 19") + bytes.fromhex("02 80 0a 00 00 00 00 00 00 00 00 80 06 00 00 00") + chunk


class SoundTests(unittest.TestCase):
    def test_independent_integration_vectors(self):
        cases = [(1, bytes([128, 129, 128])), (2, bytes([128, 129, 129]))]
        for order, expected in cases:
            self.assertEqual(integrate(bytes([128, 129, 127]), order)[0], expected)
        self.assertEqual(integrate(bytes([129, 128, 127]), 3)[0], bytes([129, 131, 133]))

    def test_original_order_zero_leaves_values_and_state_unchanged(self):
        self.assertEqual(integrate(bytes([1,128,255]),0),(bytes([1,128,255]),bytes([128]*4)))
        payload=bytearray(sound_payload(uniform(255)));payload[10]=0
        self.assertEqual(decode(bytes(payload)).samples,bytes([255])*64)

    def test_physical_terminal_bits_retained_separately_from_declared_bits(self):
        payload=bytearray(sound_payload(uniform(128)))
        struct.pack_into('<I',payload,32,5)  # header+4 stale declaredbitcount
        sound=decode(bytes(payload))
        self.assertEqual((sound.packed_bits,sound.consumed_bits,sound.terminal_unused_bits),(5,11,5))
        self.assertEqual(sound.samples,bytes([128])*64)
        self.assertEqual(sound.terminal_unused_value,0)

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
        self.assertEqual(sound.chunk_metadata, struct.pack("<H",5)+bytes(40))

    def test_default_zigzag_palette_without_local_control_bits(self):
        # Type0, p=1/e=1, max255: symbol0 maps128, escaped1+0 maps127.
        text = "00 000 000" + "010" * 32
        sound = decode(sound_payload(text))
        self.assertEqual(sound.encoded_values, bytes([128, 127]) * 32)

    def test_uninterpreted_record_byte1_retained_for_all_values(self):
        # Stream getter returns raw pointer/length; processor skips byte1.
        for value in range(256):
            payload = bytearray(sound_payload(uniform(128)))
            payload[1] = payload[13] = payload[23] = value
            sound = decode(bytes(payload))
            self.assertEqual(sound.samples, bytes([128]) * 64)
            self.assertEqual(sound.header_record_metadata[1], value)
            self.assertEqual(sound.record_metadata[1], value)
            self.assertEqual(sound.data_record_metadata[1], value)

    def test_order1_and_partial_final_block(self):
        payload = bytearray(sound_payload(uniform(128)))
        payload[10] = 1
        struct.pack_into('<I', payload, 36, 22)  # chunk+8 expanded count
        sound = decode(bytes(payload))
        self.assertEqual(sound.order, 1)
        self.assertEqual(sound.samples, bytes([128]) * 22)
        self.assertEqual(sound.block_padding, bytes([128]) * 42)

    def test_partial_block_rejects_a_trailing_extra_block(self):
        # Two independently encoded kind3 constant blocks with expanded22
        # must fail because the second block leaves unconsumed packed bits.
        payload = bytearray(sound_payload(uniform(128) + uniform(128)))
        struct.pack_into('<I', payload, 36, 22)
        with self.assertRaises(SoundError):
            decode(bytes(payload))

    def test_malformed_and_unsupported_sound(self):
        payload = sound_payload(uniform(128))
        candidates = [b"", payload[:-1]]
        for offset, value in [(0, 3), (6, 2), (7, 16), (8, 11), (10, 5), (12, 3), (20, 255), (22, 1), (30, 4), (31, 1)]:
            changed = bytearray(payload)
            changed[offset] = value
            candidates.append(bytes(changed))
        for candidate in candidates:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                decode(candidate)

    def test_native22_byte_header_retains_one_opaque_pair(self):
        original=sound_payload(uniform(128))
        chunk=bytearray(original[28:40]);struct.pack_into('<H',chunk,0,22)
        metadata=struct.pack('<HII',1,17,29)
        payload=original[:28]+chunk+metadata+original[82:]
        actual=decode(payload)
        self.assertEqual(actual.chunk_metadata,metadata)
        self.assertEqual(actual.samples,bytes([128])*64)
        for count in (0,2):
            malformed=bytearray(payload);struct.pack_into('<H',malformed,40,count)
            with self.assertRaises(SoundError):decode(bytes(malformed))
        unsupported=bytearray(payload);struct.pack_into('<H',unsupported,28,30)
        with self.assertRaises(SoundError):decode(bytes(unsupported))

    def test_source_proven_header_count_matrix_and_unindexed_variant(self):
        original=sound_payload(uniform(128))
        packed=original[82:]
        for count in range(1,27):
            metadata=struct.pack('<H',count)+bytes((i*37+11)&255 for i in range(count*8))
            chunk=struct.pack('<HBBII',14+8*count,3,2,11,64)+metadata+packed
            actual=decode(original[:28]+chunk)
            self.assertEqual(actual.chunk_metadata,metadata)
            self.assertEqual(actual.samples,bytes([128])*64)
        unindexed=original[:28]+struct.pack('<HBBII',12,3,0,11,64)+packed
        self.assertEqual(decode(unindexed).chunk_metadata,b'')
        self.assertEqual(decode(unindexed).samples,bytes([128])*64)
        for count in (0,27):
            chunk=struct.pack('<HBBIIH',14+8*count,3,2,11,64,count)+bytes(count*8)+packed
            with self.assertRaises(SoundError):decode(original[:28]+chunk)

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
