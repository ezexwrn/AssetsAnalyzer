import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED_KEYS = {
    "categories",
    "top_files",
    "top_folders",
    "duplicates_min_size",
    "signature_categories",
    "texture_oversized",
    "audio_target_kbps",
}


class ConfigTests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as config_file:
            self.config = json.load(config_file)

    def test_has_every_required_key(self):
        self.assertEqual(REQUIRED_KEYS - set(self.config), set())

    def test_extensions_are_lowercase_and_start_with_a_dot(self):
        for category, extensions in self.config["categories"].items():
            for extension in extensions:
                self.assertTrue(extension.startswith("."), f"{category}: {extension}")
                self.assertEqual(extension, extension.lower(), f"{category}: {extension}")

    def test_no_extension_belongs_to_two_categories(self):
        seen = {}
        for category, extensions in self.config["categories"].items():
            for extension in extensions:
                self.assertNotIn(extension, seen, f"{extension} in {seen.get(extension)} and {category}")
                seen[extension] = category

    def test_signature_categories_exist(self):
        valid = set(self.config["categories"]) | {"other"}
        self.assertTrue(set(self.config["signature_categories"]) <= valid)


if __name__ == "__main__":
    unittest.main()