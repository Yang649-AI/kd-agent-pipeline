import sys
import unittest
from pathlib import Path

from langchain_core.documents import Document


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent.ask_system_once import (
    build_embedding_model_kwargs,
    build_result_record,
    configure_offline_huggingface,
    extract_command_patterns,
    extract_direct_contact_answer,
    extract_query_symbols,
    format_human_readable,
    is_acc_24e3_query,
    lexical_acc_hardware_score,
    lexical_command_score,
    lexical_contact_score,
    lexical_symbol_score,
    merge_retrieved_docs,
    parse_question,
)


class AskSystemOnceTest(unittest.TestCase):
    def test_parse_question_joins_positional_words(self):
        question = parse_question(["What", "is", "a", "PLC?"])

        self.assertEqual(question, "What is a PLC?")

    def test_parse_question_rejects_empty_question(self):
        with self.assertRaises(ValueError):
            parse_question(["", "   "])

    def test_configure_offline_huggingface_sets_local_cache_flags(self):
        env = {}

        configure_offline_huggingface(env)

        self.assertEqual(env["HF_HUB_OFFLINE"], "1")
        self.assertEqual(env["TRANSFORMERS_OFFLINE"], "1")
        self.assertEqual(env["HF_DATASETS_OFFLINE"], "1")
        self.assertEqual(env["HF_HUB_DISABLE_TELEMETRY"], "1")

    def test_build_embedding_model_kwargs_forces_local_files_only(self):
        kwargs = build_embedding_model_kwargs("cuda")

        self.assertEqual(kwargs["device"], "cuda")
        self.assertIs(kwargs["local_files_only"], True)

    def test_lexical_contact_score_boosts_email_support_chunks(self):
        doc = Document(
            page_content=(
                "Technical Support Phone: Call 1-800-556-6766. "
                "Email: ODT-Support@omron.com Alternate Email: ia.techsupport@omron.com"
            ),
            metadata={"citation_anchor": "O015-E-01.pdf#page=1"},
        )

        score = lexical_contact_score(
            "What email address is listed for technical support?",
            doc,
        )

        self.assertGreaterEqual(score, 6)

    def test_extract_query_symbols_finds_power_pmac_variable_names(self):
        symbols = extract_query_symbols("What is the purpose of Motor[x].Servo.Kp?")

        self.assertEqual(symbols, ["Motor[x].Servo.Kp"])

    def test_lexical_symbol_score_boosts_exact_variable_description(self):
        doc = Document(
            page_content=(
                "Motor[x].Servo.Kp Description: PID proportional gain term. "
                "Motor[x].Servo.Kp is the servo loop's main proportional gain term, "
                "providing a control output proportional to the position error."
            ),
            metadata={"citation_anchor": "manual.pdf#page=566"},
        )

        score = lexical_symbol_score("What is the purpose of Motor[x].Servo.Kp?", doc)

        self.assertGreaterEqual(score, 8)

    def test_extract_command_patterns_finds_power_pmac_command_syntax(self):
        cases = {
            "What does the I{data}-> command report?": ["I{data}->"],
            "What is the function of the undefine all command?": ["undefine all"],
            "What does the v command report in Power PMAC?": ["v"],
            "What does the vers command return?": ["vers"],
        }

        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertEqual(extract_command_patterns(question), expected)

    def test_lexical_command_score_boosts_exact_command_reference(self):
        doc = Document(
            page_content=(
                "I{data}-> reports the value of an I-variable. "
                "This command returns the current setting for the requested variable."
            ),
            metadata={"citation_anchor": "manual.pdf#page=95"},
        )

        score = lexical_command_score("What does the I{data}-> command report?", doc)

        self.assertGreaterEqual(score, 8)

    def test_lexical_command_score_does_not_match_short_commands_inside_words(self):
        noisy_doc = Document(
            page_content=(
                "This overview describes velocity values, versions, and vector functions "
                "without documenting the short online command."
            ),
            metadata={"citation_anchor": "manual.pdf#page=10"},
        )
        command_doc = Document(
            page_content=(
                "Function: Report actual velocity values. Syntax: The v command causes "
                "Power PMAC to report actual velocities."
            ),
            metadata={"citation_anchor": "manual.pdf#page=1232"},
        )

        noisy_score = lexical_command_score(
            "What does the v command report in Power PMAC?",
            noisy_doc,
        )
        command_score = lexical_command_score(
            "What does the v command report in Power PMAC?",
            command_doc,
        )

        self.assertEqual(noisy_score, 0)
        self.assertGreaterEqual(command_score, 10)

    def test_lexical_command_score_prefers_command_spec_over_mentions(self):
        mention_doc = Document(
            page_content="The firmware version can be queried with the vers command.",
            metadata={"citation_anchor": "manual.pdf#page=1080"},
        )
        spec_doc = Document(
            page_content=(
                "Power PMAC On-Line Command Specification vers Function: Report "
                "firmware version Scope: Global Syntax: vers The vers command causes "
                "Power PMAC to report the version number string."
            ),
            metadata={"citation_anchor": "manual.pdf#page=1233"},
        )

        mention_score = lexical_command_score("What does the vers command return?", mention_doc)
        spec_score = lexical_command_score("What does the vers command return?", spec_doc)

        self.assertGreater(spec_score, mention_score)

    def test_is_acc_24e3_query_accepts_hyphenated_and_spaced_forms(self):
        self.assertTrue(is_acc_24e3_query("What is the ACC-24E3 used for?"))
        self.assertTrue(is_acc_24e3_query("What can ACC 24E3 process?"))
        self.assertFalse(is_acc_24e3_query("What is Motor[x].Servo.Kp?"))

    def test_lexical_acc_hardware_score_prefers_acc_24e3_hardware_manual(self):
        question = "How many channels of axis interface can ACC-24E3 provide?"
        hardware_doc = Document(
            page_content="The ACC-24E3 provides four channels of axis interface circuitry.",
            metadata={
                "source_file": "_info_OMRON_Delta_Tau_ACC_24E3_Manual_2024314151533.pdf",
                "citation_anchor": "_info_OMRON_Delta_Tau_ACC_24E3_Manual_2024314151533.pdf#page=7",
            },
        )
        software_doc = Document(
            page_content="ACC24E3[i] contains software gate register descriptions.",
            metadata={
                "source_file": "Power PMAC Software Reference Manual.pdf",
                "citation_anchor": "Power PMAC Software Reference Manual.pdf#page=952",
            },
        )

        hardware_score = lexical_acc_hardware_score(question, hardware_doc)
        software_score = lexical_acc_hardware_score(question, software_doc)

        self.assertGreaterEqual(hardware_score, 12)
        self.assertGreater(hardware_score, software_score)

    def test_lexical_acc_hardware_score_prefers_body_text_over_table_of_contents(self):
        question = "What is the ACC-24E3 used for?"
        toc_doc = Document(
            page_content=(
                "DELTA TAU ACC-24E3 USER'S MANUAL TABLE OF CONTENTS "
                "Digital Feedback Mezzanine Board."
            ),
            metadata={
                "source_file": "_info_OMRON_Delta_Tau_ACC_24E3_Manual_2024314151533.pdf",
                "citation_anchor": "_info_OMRON_Delta_Tau_ACC_24E3_Manual_2024314151533.pdf#page=5",
            },
        )
        body_doc = Document(
            page_content=(
                "Introduction The ACC-24E3 family of products provides a powerful "
                "and flexible suite of axis-interface circuitry for UMAC racks."
            ),
            metadata={
                "source_file": "_info_OMRON_Delta_Tau_ACC_24E3_Manual_2024314151533.pdf",
                "citation_anchor": "_info_OMRON_Delta_Tau_ACC_24E3_Manual_2024314151533.pdf#page=8",
            },
        )

        toc_score = lexical_acc_hardware_score(question, toc_doc)
        body_score = lexical_acc_hardware_score(question, body_doc)

        self.assertGreater(body_score, toc_score)

    def test_merge_retrieved_docs_prepends_high_scoring_lexical_doc(self):
        vector_doc = Document(
            page_content="Unrelated software reference material.",
            metadata={"citation_anchor": "manual.pdf#page=1503"},
        )
        lexical_doc = Document(
            page_content="Email: support@example.com",
            metadata={"citation_anchor": "manual.pdf#page=1"},
        )

        merged = merge_retrieved_docs(
            vector_docs=[vector_doc],
            lexical_docs=[(10, lexical_doc)],
            limit=2,
        )

        self.assertEqual(merged[0].metadata["citation_anchor"], "manual.pdf#page=1")
        self.assertEqual(merged[1].metadata["citation_anchor"], "manual.pdf#page=1503")

    def test_extract_direct_contact_answer_returns_phone_without_ollama(self):
        docs = [
            Document(
                page_content=(
                    "Technical Support Phone: Call 1-800-556-6766, and follow "
                    "the prompts for technical support on PMAC products. "
                    "Email: ODT-Support@omron.com"
                ),
                metadata={
                    "citation_anchor": "O015-E-01_Power PMAC Software Reference Manual.pdf#page=1"
                },
            )
        ]

        answer = extract_direct_contact_answer(
            "What Phone number is listed for technical support?",
            docs,
        )

        self.assertIsNotNone(answer)
        self.assertIn("1-800-556-6766", answer)
        self.assertIn("O015-E-01_Power PMAC Software Reference Manual.pdf#page=1", answer)

    def test_extract_direct_contact_answer_returns_all_support_emails(self):
        docs = [
            Document(
                page_content=(
                    "Email: ODT-Support@omron.com Alternate Email: "
                    "ia.techsupport@omron.com"
                ),
                metadata={"citation_anchor": "manual.pdf#page=1"},
            )
        ]

        answer = extract_direct_contact_answer(
            "What email address is listed for technical support?",
            docs,
        )

        self.assertIsNotNone(answer)
        self.assertIn("ODT-Support@omron.com", answer)
        self.assertIn("ia.techsupport@omron.com", answer)
        self.assertIn("manual.pdf#page=1", answer)

    def test_build_result_record_includes_retrieved_citations(self):
        docs = [
            Document(
                page_content="Only qualified personnel should handle this equipment.",
                metadata={
                    "source_file": "Power PMAC Software Reference Manual.pdf",
                    "page": 2,
                    "citation_anchor": "Power PMAC Software Reference Manual.pdf#page=2",
                    "chunk_id": "chunk-2",
                    "discipline": "power_pmac",
                    "content_type": "text",
                    "text_length": 64,
                },
            )
        ]

        result = build_result_record(
            question="Who should handle this equipment?",
            answer="Answer:\nQualified personnel.\nReferences:\n- Power PMAC Software Reference Manual.pdf#page=2",
            docs=docs,
            latency_sec=1.25,
            input_tokens=120,
            output_tokens=20,
            response_mode="ollama",
        )

        self.assertEqual(result["id"], "manual")
        self.assertEqual(result["question"], "Who should handle this equipment?")
        self.assertEqual(result["response_mode"], "ollama")
        self.assertEqual(result["total_tokens"], 140)
        self.assertEqual(
            result["retrieved"][0]["citation_anchor"],
            "Power PMAC Software Reference Manual.pdf#page=2",
        )
        self.assertIn("Only qualified personnel", result["retrieved"][0]["content_preview"])

    def test_format_human_readable_does_not_duplicate_answer_heading(self):
        result = {
            "question": "What is the support phone number?",
            "answer": "Answer:\n(818) 717-5656\nReferences:\n- Power PMAC Software Reference Manual.pdf#page=1",
            "retrieved": [
                {
                    "source_file": "Power PMAC Software Reference Manual.pdf",
                    "page": 1,
                    "citation_anchor": "Power PMAC Software Reference Manual.pdf#page=1",
                }
            ],
            "response_mode": "ollama",
            "latency_sec": 1.2,
            "total_tokens": 300,
        }

        text = format_human_readable(result)

        self.assertIn("Result:\nAnswer:", text)
        self.assertNotIn("Answer:\nAnswer:", text)


if __name__ == "__main__":
    unittest.main()
