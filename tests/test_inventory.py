import os
import tempfile
import unittest

from modules import inventory
from tests.helpers import write_file

CATEGORIES = {"textures": {".dds"}, "audio": {".wav"}}


class InventoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = temp.name
        write_file(self.root, "Textures/a.DDS", b"x" * 100)
        write_file(self.root, "Audio/b.wav", b"x" * 300)
        write_file(self.root, "Audio/c.wav", b"x" * 50)
        write_file(self.root, "readme.xyz", b"x" * 10)
        self.files = inventory.scan(self.root, CATEGORIES)

    def test_scan_finds_all_files(self):
        self.assertEqual(len(self.files), 4)

    def test_category_ignores_case_and_defaults_to_other(self):
        by_path = {file["path"]: file["category"] for file in self.files}
        self.assertEqual(by_path[os.path.join("Textures", "a.DDS")], "textures")
        self.assertEqual(by_path["readme.xyz"], "other")

    def test_summary_by_category(self):
        summary = inventory.summary_by_category(self.files)
        self.assertEqual(summary["audio"], {"count": 2, "size": 350})
        self.assertEqual(summary["textures"], {"count": 1, "size": 100})
        self.assertEqual(summary["other"], {"count": 1, "size": 10})

    def test_summary_by_folder_groups_root_files(self):
        summary = inventory.summary_by_folder(self.files)
        self.assertEqual(summary["Audio"], {"count": 2, "size": 350})
        self.assertEqual(summary["(root)"], {"count": 1, "size": 10})

    def test_summary_by_extension_only_counts_the_requested_category(self):
        summary = inventory.summary_by_extension(self.files, "other")
        self.assertEqual(summary, {".xyz": {"count": 1, "size": 10}})

    def test_heaviest_is_sorted_and_limited(self):
        top = inventory.heaviest(self.files, 2)
        self.assertEqual([file["size"] for file in top], [300, 100])


if __name__ == "__main__":
    unittest.main()