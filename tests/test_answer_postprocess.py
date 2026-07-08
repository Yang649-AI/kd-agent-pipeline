import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent.answer_postprocess import clean_ollama_answer


class AnswerPostprocessTest(unittest.TestCase):
    def test_removes_qwen_thinking_tags_from_not_found_answer(self):
        raw = (
            "Answer:\n"
            "未找到参考资料\n\n"
            "References:\n"
            " /think\n"
            "</think>\n\n"
            "Answer:\n"
            "未找到参考资料\n\n"
            "References:\n"
            " Power PMAC Software Reference Manual.pdf#page=1113"
        )

        cleaned = clean_ollama_answer(raw)

        self.assertNotIn("/think", cleaned)
        self.assertNotIn("</think>", cleaned)
        self.assertEqual(cleaned.count("Answer:"), 1)
        self.assertIn("未找到参考资料", cleaned)
        self.assertIn("Power PMAC Software Reference Manual.pdf#page=1113", cleaned)

    def test_removes_xml_think_block_before_answer(self):
        raw = (
            "<think>\n"
            "I should inspect the context.\n"
            "</think>\n\n"
            "Answer: Use qualified personnel.\n"
            "References:\n"
            " Power PMAC Software Reference Manual.pdf#page=2"
        )

        cleaned = clean_ollama_answer(raw)

        self.assertNotIn("I should inspect", cleaned)
        self.assertEqual(
            cleaned,
            "Answer: Use qualified personnel.\n"
            "References:\n"
            " Power PMAC Software Reference Manual.pdf#page=2",
        )


if __name__ == "__main__":
    unittest.main()
