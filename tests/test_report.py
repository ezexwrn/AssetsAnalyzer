import unittest

from modules import report


class ReportTests(unittest.TestCase):
    def test_format_size(self):
        self.assertEqual(report.format_size(0), "0.0 B")
        self.assertEqual(report.format_size(1536), "1.5 KB")
        self.assertEqual(report.format_size(5 * 1024 ** 2), "5.0 MB")
        self.assertEqual(report.format_size(1024 ** 3), "1.0 GB")

    def test_compare_orders_biggest_savings_first(self):
        old = {"categories": {"audio": {"size": 100}, "video": {"size": 50}}}
        new = {"categories": {"audio": {"size": 40}, "textures": {"size": 10}}}
        self.assertEqual(
            report.compare(old, new),
            [("audio", 100, 40, -60), ("video", 50, 0, -50), ("textures", 0, 10, 10)],
        )

    def test_compare_identical_reports_has_no_difference(self):
        data = {"categories": {"audio": {"size": 100}}}
        self.assertEqual(report.compare(data, data), [("audio", 100, 100, 0)])


if __name__ == "__main__":
    unittest.main()