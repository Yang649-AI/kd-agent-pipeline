import sys
import unittest
from pathlib import Path

from langchain_core.documents import Document


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent.run_system_rag import SYSTEM_PROMPT, format_docs


class SystemPromptTest(unittest.TestCase):
    def test_system_prompt_is_readable_and_grounded(self):
        mojibake_markers = ["浣犳槸", "妫€", "璧勬枡", "鍥炵瓟"]

        for marker in mojibake_markers:
            self.assertNotIn(marker, SYSTEM_PROMPT)

        self.assertIn("Answer only from the retrieved context", SYSTEM_PROMPT)
        self.assertIn("No supporting reference found", SYSTEM_PROMPT)
        self.assertIn("Do not output chain-of-thought", SYSTEM_PROMPT)

    def test_format_docs_uses_readable_labels(self):
        docs = [
            Document(
                page_content="Qualified personnel must install the equipment.",
                metadata={
                    "source_file": "Power PMAC Software Reference Manual.pdf",
                    "page": 2,
                    "citation_anchor": "Power PMAC Software Reference Manual.pdf#page=2",
                    "chunk_id": "chunk-1",
                    "content_type": "text",
                },
            )
        ]

        context = format_docs(docs)

        self.assertIn("Source file: Power PMAC Software Reference Manual.pdf", context)
        self.assertIn("Page: 2", context)
        self.assertIn("Citation anchor: Power PMAC Software Reference Manual.pdf#page=2", context)
        self.assertIn("Text:", context)


if __name__ == "__main__":
    unittest.main()
