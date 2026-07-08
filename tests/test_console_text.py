import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.console_text import sanitize_for_console


class ConsoleTextTest(unittest.TestCase):
    def test_preserves_ascii_text(self):
        self.assertEqual(sanitize_for_console("Answer: hello", "gbk"), "Answer: hello")

    def test_replaces_unencodable_characters(self):
        self.assertEqual(
            sanitize_for_console("Copyright © 2019", "gbk"),
            "Copyright ? 2019",
        )


if __name__ == "__main__":
    unittest.main()
