import unittest

from smart_clicker.cli import main


class CliTests(unittest.TestCase):
    def test_main_returns_success(self):
        self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main()
