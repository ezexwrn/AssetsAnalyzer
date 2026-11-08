import struct
import tempfile
import unittest

from modules import inventory, textures
from tests.helpers import write_file


def png_bytes(width, height, bit_depth=8, color_type=6):
    signature = bytes.fromhex("89504E470D0A1A0A")
    return (
        signature
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
        + bytes([bit_depth, color_type, 0, 0, 0])
    )


def dds_bytes(width, height, mipmaps=1, fourcc=b"DXT5"):
    header = bytearray(128)
    header[0:4] = b"DDS "
    struct.pack_into("<I", header, 4, 124)
    struct.pack_into("<II", header, 12, height, width)
    struct.pack_into("<I", header, 28, mipmaps)
    if fourcc is None:
        struct.pack_into("<I", header, 80, 0x41)
        struct.pack_into("<I", header, 88, 32)
    else:
        struct.pack_into("<I", header, 80, 0x4)
        header[84:88] = fourcc
    return bytes(header)


def tga_bytes(width, height, bits_per_pixel=32, image_type=2):
    header = bytearray(18)
    header[2] = image_type
    struct.pack_into("<HH", header, 12, width, height)
    header[16] = bits_per_pixel
    return bytes(header)


def bmp_bytes(width, height, bits_per_pixel=24):
    header = bytearray(54)
    header[0:2] = b"BM"
    struct.pack_into("<I", header, 14, 40)
    struct.pack_into("<ii", header, 18, width, height)
    struct.pack_into("<H", header, 28, bits_per_pixel)
    return bytes(header)


class TexturesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = temp.name

    def read(self, name, content):
        path = write_file(self.root, name, content)
        return textures.read_texture(path, "." + name.rsplit(".", 1)[1])

    def test_png(self):
        info = self.read("a.png", png_bytes(3840, 2160))
        self.assertEqual(info, {"width": 3840, "height": 2160, "detail": "8-bit rgba"})

    def test_dds_compressed(self):
        info = self.read("a.dds", dds_bytes(1024, 512, mipmaps=4))
        self.assertEqual(info, {"width": 1024, "height": 512, "detail": "DXT5, 4 mips"})

    def test_dds_uncompressed_without_mipmaps(self):
        info = self.read("a.dds", dds_bytes(256, 256, mipmaps=0, fourcc=None))
        self.assertEqual(info["detail"], "uncompressed 32-bit, 1 mips")

    def test_tga_raw_and_rle(self):
        self.assertEqual(self.read("a.tga", tga_bytes(64, 32))["detail"], "32-bit raw")
        self.assertEqual(self.read("b.tga", tga_bytes(64, 32, 24, 10))["detail"], "24-bit RLE")

    def test_bmp_with_negative_height(self):
        info = self.read("a.bmp", bmp_bytes(1024, -768))
        self.assertEqual(info, {"width": 1024, "height": 768, "detail": "24-bit"})

    def test_garbage_is_not_a_texture(self):
        self.assertIsNone(self.read("a.png", b"this is not a png"))
        self.assertIsNone(self.read("a.dds", b"DDS tiny"))
        self.assertIsNone(self.read("a.tga", bytes([0xFF] * 40)))
        self.assertIsNone(self.read("a.bmp", b"BM"))

    def test_summarize_flags_oversized_textures(self):
        write_file(self.root, "big.png", png_bytes(4096, 2048))
        write_file(self.root, "small.dds", dds_bytes(1024, 1024))
        write_file(self.root, "broken.tga", bytes([0xFF] * 40))
        write_file(self.root, "notes.txt", b"hello")
        files = inventory.scan(self.root, {})
        results = {item["path"]: item for item in textures.summarize(files, self.root, 2048)}
        self.assertEqual(set(results), {"big.png", "small.dds"})
        self.assertTrue(results["big.png"]["oversized"])
        self.assertFalse(results["small.dds"]["oversized"])


if __name__ == "__main__":
    unittest.main()