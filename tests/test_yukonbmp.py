"""Hand-authored bitstreams and pixels, independent of original game media."""
import struct
import unittest
import zlib

from tools.yukonbmp import BitmapError, Bits, Frame, decode, png, unpack, values
from tools.compare_bitmap_capture import compare, read_rgb_capture


def bits(text):
    text = text.replace(" ", "")
    return int(text.ljust((len(text) + 7) // 8 * 8, "0"), 2).to_bytes((len(text) + 7) // 8, "big")


def packed(text, size=64, palette=b"\x0a\x14\x1e\x28"):
    text = text.replace(" ", "")
    return struct.pack("<HBBII", 12, 3, 1, len(text), size) + bytes([len(palette) - 1]) + palette + bits(text)


def uniform(value, repeat=0):
    return "11" + f"{value:08b}" + ("1" + f"{repeat:016b}" if repeat else "0")


def resource(width, height, chunk):
    return struct.pack("<HHHII", 1, width, height, 14, len(chunk)) + chunk


class IntegerTests(unittest.TestCase):
    def test_msb_first_and_nonzero_offset(self):
        reader = Bits(bytes.fromhex("12345678"), 32, 4)
        self.assertEqual(reader.get(8), 0x23)
        self.assertEqual(reader.position, 12)

    def test_escape_symbols(self):
        reader = Bits(bits("00 01 10 110 111"), 12)
        self.assertEqual(values(reader, 2, 1, 4, 5, False), bytes(range(5)))
        self.assertEqual(reader.position, 12)

    def test_hybrid_small_middle_and_final_groups(self):
        text = "10 11 010 011 0000 0001 0010 0011"
        reader = Bits(bits(text), 26)
        self.assertEqual(values(reader, 2, 1, 7, 8), bytes(range(8)))
        self.assertEqual(reader.position, 26)

    def test_hybrid_falls_back_to_escape(self):
        self.assertEqual(values(Bits(bits("00 01 10 11"), 8), 2, 1, 3, 4), bytes(range(4)))

    def test_zero_group_small_prefix(self):
        # Native groups=0 is allowed; the small prefix still emits zero.
        self.assertEqual(values(Bits(b"\xff", 8), 1, 8, 4, 8), bytes(8))

    def test_palette_overflow(self):
        with self.assertRaises(BitmapError):
            values(Bits(bits("11 1"), 3), 2, 1, 2, 1, False)

    def test_escape_truncation(self):
        with self.assertRaises(BitmapError):
            values(Bits(bits("11 1"), 3), 2, 1, 7, 1, False)

    def test_invalid_parameters(self):
        for parameters in [(0, 1, 1, 1), (1, 9, 1, 1), (1, 1, 256, 1), (1, 1, 1, 0), (1, 1, 1, 65)]:
            with self.subTest(parameters=parameters), self.assertRaises(BitmapError):
                values(Bits(b"\0", 8), *parameters)


class BitmapTests(unittest.TestCase):
    def test_uniform_and_repeat(self):
        self.assertEqual(unpack(packed(uniform(72, 2), 192), 192), bytes([72]) * 192)

    def test_absolute_reference_restores_outer_cursor(self):
        text = uniform(72) + "10" + "0" * 24 + uniform(19)
        self.assertEqual(unpack(packed(text, 192), 192), bytes([72]) * 128 + bytes([19]) * 64)

    def test_reference_cycle(self):
        with self.assertRaisesRegex(BitmapError, "cyclic"):
            unpack(packed("10" + "0" * 24), 64)

    def test_reference_outside_declared_bits(self):
        with self.assertRaises(BitmapError):
            unpack(packed("10" + f"{100:024b}"), 64)

    def test_column_major_tiles_and_edge_cropping(self):
        chunk = packed("".join(uniform(value) for value in [10, 20, 30, 40]), 256)
        frame = decode(resource(9, 9, chunk))[0]
        self.assertEqual(frame.pixels, (bytes([10]) * 8 + bytes([30])) * 8 + bytes([20]) * 8 + bytes([40]))

    def test_global_palette_block(self):
        text = "00 00 001 000 " + "00 01 10 11 " * 16
        self.assertEqual(unpack(packed(text), 64), bytes([10, 20, 30, 40]) * 16)

    def test_local_cumulative_palette(self):
        # Type0, control1, two palette tokens 0/1 => global indices0/2.
        text = "00 01 000010 000 000 101 000 000 " + "01" * 32
        self.assertEqual(unpack(packed(text), 64), bytes([10, 30]) * 32)

    def test_local_delta_reset_palette(self):
        # Tokens 1,1,0,3 => indices1,2,3; zero consumes the reset token.
        symbols = ("00 01 10 " * 21) + "00"
        text = "00 10 000100 001 000 01010011 001 000 " + symbols
        self.assertEqual(unpack(packed(text), 64), bytes([20, 30, 40]) * 21 + bytes([20]))

    def test_unsupported_palette_control(self):
        with self.assertRaisesRegex(BitmapError, "control 3"):
            unpack(packed("00 11"), 64)

    def test_repeat_overflow(self):
        with self.assertRaisesRegex(BitmapError, "repeat"):
            unpack(packed(uniform(72, 1)), 64)

    def test_unsupported_compression(self):
        for offset, value in [(0, 13), (2, 4), (3, 2)]:
            chunk = bytearray(packed(uniform(1)))
            chunk[offset] = value
            with self.subTest(offset=offset), self.assertRaises(BitmapError):
                unpack(bytes(chunk), 64)

    def test_declared_length_and_trailing_data(self):
        chunk = packed(uniform(1))
        for data, size in [(chunk[:-1], 64), (chunk + b"\0", 64), (chunk, 128), (packed(uniform(1) + "0"), 64)]:
            with self.subTest(data=data), self.assertRaises(BitmapError):
                unpack(data, size)

    def test_invalid_frame_ranges_and_dimensions(self):
        chunk = packed(uniform(1))
        for data in [b"", b"\0\0", resource(0, 8, chunk), resource(8, 0x8000, chunk), resource(8, 8, chunk)[:-1], struct.pack("<HHHII", 1, 8, 8, 1, len(chunk)) + chunk]:
            with self.subTest(data=data), self.assertRaises(BitmapError):
                decode(data)

    def test_png_keeps_indices_and_palette_without_inventing_alpha(self):
        palette = bytes(range(256)) * 3
        image = png(Frame(2, 1, 0, 0, b"\x03\xff"), palette)
        position, chunks = 8, {}
        while position < len(image):
            size = struct.unpack_from(">I", image, position)[0]
            kind = image[position + 4:position + 8]
            chunks[kind] = image[position + 8:position + 8 + size]
            position += 12 + size
        self.assertEqual(chunks[b"PLTE"], palette)
        self.assertEqual(zlib.decompress(chunks[b"IDAT"]), b"\0\x03\xff")
        self.assertNotIn(b"tRNS", chunks)


def rgb_png(filter_kind, encoded):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes([filter_kind]) + encoded[0] + bytes([filter_kind]) + encoded[1])) + chunk(b"IEND", b""))


class CaptureTests(unittest.TestCase):
    def test_all_png_filters_with_independent_encoded_rows(self):
        encoded = [
            (b"\x0a\x14\x1e\x0f\x19\x23", b"\x14\x1e\x28\x19\x23\x2d"),
            (b"\x0a\x14\x1e\x05\x05\x05", b"\x14\x1e\x28\x05\x05\x05"),
            (b"\x0a\x14\x1e\x0f\x19\x23", b"\x0a\x0a\x0a\x0a\x0a\x0a"),
            (b"\x0a\x14\x1e\x0a\x0f\x14", b"\x0f\x14\x19\x08\x08\x08"),
            (b"\x0a\x14\x1e\x05\x05\x05", b"\x0a\x0a\x0a\x05\x05\x05"),
        ]
        expected = bytes([10, 20, 30, 15, 25, 35, 20, 30, 40, 25, 35, 45])
        for kind, rows in enumerate(encoded):
            with self.subTest(kind=kind):
                self.assertEqual(read_rgb_capture(rgb_png(kind, rows)), (2, 2, expected))

    def test_capture_crc_and_truncation(self):
        image = rgb_png(0, (bytes(6), bytes(6)))
        for data in [image[:-1], image[:40] + bytes([image[40] ^ 1]) + image[41:]]:
            with self.assertRaises(ValueError):
                read_rgb_capture(data)

    def test_comparison_exclusions_and_dac_conversion(self):
        palette = bytearray(768)
        palette[3:6] = bytes([254, 6, 16])
        frame = Frame(3, 1, 0, 0, bytes([0, 1, 159]))
        result = compare(frame, palette, (3, 1, bytes([1, 2, 3, 255, 4, 16, 4, 5, 6])), 0, 0)
        self.assertEqual(result["border_pixels"], 1)
        self.assertEqual(result["mismatches"], 0)
        self.assertEqual(result["excluded_exterior"], 1)
        self.assertEqual(result["excluded_interior"], 1)


if __name__ == "__main__":
    unittest.main()
