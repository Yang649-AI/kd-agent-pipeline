import sys
import unittest
from pathlib import Path

from langchain_core.documents import Document


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent.system_fallback import build_extractive_fallback_answer


class SystemRagFallbackTest(unittest.TestCase):
    def test_returns_not_found_when_no_docs_exist(self):
        answer = build_extractive_fallback_answer([])
        self.assertEqual(answer, "未找到参考资料")

    def test_builds_answer_and_references_from_top_doc(self):
        docs = [
            Document(
                page_content=(
                    "Qualified personnel must transport, assemble, install, and maintain "
                    "this equipment. Never disconnect or connect the product while the "
                    "power source is energized to avoid electric arcing."
                ),
                metadata={
                    "source_file": "Power PMAC Software Reference Manual.pdf",
                    "page": 2,
                    "citation_anchor": "Power PMAC Software Reference Manual.pdf#page=2",
                },
            )
        ]

        answer = build_extractive_fallback_answer(docs)

        self.assertIn("Answer:", answer)
        self.assertIn("References:", answer)
        self.assertIn("Qualified personnel must transport", answer)
        self.assertIn("Never disconnect or connect the product", answer)
        self.assertIn("Power PMAC Software Reference Manual.pdf#page=2", answer)


if __name__ == "__main__":
    unittest.main()
