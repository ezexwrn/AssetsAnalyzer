import os
import tempfile
import unittest

from modules import inventory, signatures
from tests.helpers import write_file


class SignaturesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = temp.name

    def detect(self, content):
        return signatures.detect(write_file(self.root, "sample.bin", content))

    def test_wav_is_detected_before_generic_riff(self):
        self.assertEqual(self.detect(b"RIFF" + bytes(4) + b"WAVE" + bytes(8)), "wav")

    def test_other_riff_files_use_the_generic_label(self):
        self.assertEqual(self.detect(b"RIFF" + bytes(4) + b"XXXX"), "riff (other)")

    def test_common_formats(self):
        self.assertEqual(self.detect(b"OggS" + bytes(10)), "ogg")
        self.assertEqual(self.detect(b"MZ" + bytes(20)), "exe/dll (MZ)")
        self.assertEqual(self.detect(bytes.fromhex("89504E470D0A1A0A") + bytes(8)), "png")
        self.assertEqual(self.detect(b"MSCF" + bytes(8)), "cab")

    def test_empty_file(self):
        self.assertEqual(self.detect(b""), "empty")

    def test_unknown_text_prefix_is_shown_as_text(self):
        self.assertEqual(self.detect(b"ABCDEFGH"), 'unknown "ABCD"')

    def test_unknown_binary_prefix_is_shown_as_hex(self):
        self.assertEqual(self.detect(bytes([0, 1, 2, 3, 4, 5])), "unknown 00010203")

    def test_missing_file_is_unreadable(self):
        self.assertEqual(signatures.detect(os.path.join(self.root, "missing.bin")), "unreadable")

    def test_summarize_groups_by_extension_and_label(self):
        write_file(self.root, "a.bin", b"OggS" + bytes(4))
        write_file(self.root, "b.bin", b"OggS" + bytes(4))
        write_file(self.root, "c.bin", b"ABCDEFGH")
        write_file(self.root, "d.txt", b"OggS" + bytes(4))
        files = inventory.scan(self.root, {"packed": {".bin"}})
        result = signatures.summarize(files, self.root, {"packed"})
        self.assertEqual(result[".bin"]["ogg"], {"count": 2, "size": 16})
        self.assertEqual(result[".bin"]['unknown "ABCD"'], {"count": 1, "size": 8})
        self.assertNotIn(".txt", result)


if __name__ == "__main__":
    unittest.main()