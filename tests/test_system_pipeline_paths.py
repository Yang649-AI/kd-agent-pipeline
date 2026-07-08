import os
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.paths import PROJECT_ROOT as RESOLVED_PROJECT_ROOT
from common.system_pipeline_paths import resolve_system_pipeline_paths


class SystemPipelinePathsTest(unittest.TestCase):
    def test_uses_default_paths_without_overrides(self):
        env = {}

        paths = resolve_system_pipeline_paths(env)

        self.assertEqual(
            paths.eval_path,
            RESOLVED_PROJECT_ROOT / "data" / "eval" / "baseline_smoke_questions.jsonl",
        )
        self.assertEqual(
            paths.output_path,
            RESOLVED_PROJECT_ROOT / "outputs" / "system" / "system_results.jsonl",
        )
        self.assertEqual(
            paths.report_path,
            RESOLVED_PROJECT_ROOT / "reports" / "system_pipeline_smoke_test.md",
        )

    def test_uses_env_overrides_for_custom_system_run(self):
        env = {
            "KD_AGENT_SYSTEM_EVAL_PATH": str(
                RESOLVED_PROJECT_ROOT / "data" / "eval" / "power_pmac_smoke_questions.jsonl"
            ),
            "KD_AGENT_SYSTEM_OUTPUT_PATH": str(
                RESOLVED_PROJECT_ROOT / "outputs" / "system" / "power_pmac_results.jsonl"
            ),
            "KD_AGENT_SYSTEM_REPORT_PATH": str(
                RESOLVED_PROJECT_ROOT / "reports" / "power_pmac_system_report.md"
            ),
        }

        paths = resolve_system_pipeline_paths(env)

        self.assertEqual(
            paths.eval_path,
            RESOLVED_PROJECT_ROOT / "data" / "eval" / "power_pmac_smoke_questions.jsonl",
        )
        self.assertEqual(
            paths.output_path,
            RESOLVED_PROJECT_ROOT / "outputs" / "system" / "power_pmac_results.jsonl",
        )
        self.assertEqual(
            paths.report_path,
            RESOLVED_PROJECT_ROOT / "reports" / "power_pmac_system_report.md",
        )


if __name__ == "__main__":
    unittest.main()
