import os
import tempfile
import unittest

from modules import duplicates, inventory
from tests.helpers import write_file


class DuplicatesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = temp.name
        write_file(self.root, "a.bin", b"A" * 100)
        write_file(self.root, "sub/b.bin", b"A" * 100)
        write_file(self.root, "c.bin", b"B" * 100)
        write_file(self.root, "tiny1.bin", b"Z" * 5)
        write_file(self.root, "tiny2.bin", b"Z" * 5)
        self.files = inventory.scan(self.root, {})

    def test_finds_identical_files_and_ignores_same_size_with_other_content(self):
        groups = duplicates.find(self.files, self.root, 10)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["size"], 100)
        self.assertEqual(sorted(groups[0]["paths"]), ["a.bin", os.path.join("sub", "b.bin")])

    def test_min_size_filters_small_files(self):
        self.assertEqual(len(duplicates.find(self.files, self.root, 10)), 1)
        self.assertEqual(len(duplicates.find(self.files, self.root, 1)), 2)

    def test_recoverable_size_counts_every_copy_but_one(self):
        groups = [{"size": 10, "paths": ["a", "b", "c"]}, {"size": 5, "paths": ["d", "e"]}]
        self.assertEqual(duplicates.recoverable_size(groups), 25)

    def test_recoverable_size_without_groups_is_zero(self):
        self.assertEqual(duplicates.recoverable_size([]), 0)


if __name__ == "__main__":
    unittest.main()