import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from common.paths import PROJECT_ROOT


@dataclass(frozen=True)
class SystemPipelinePaths:
    eval_path: Path
    output_path: Path
    report_path: Path


def _resolve_path(env: Mapping[str, str], key: str, default: Path) -> Path:
    value = env.get(key)
    if not value:
        return default
    return Path(value).expanduser().resolve()


def resolve_system_pipeline_paths(
    env: Mapping[str, str] | None = None,
) -> SystemPipelinePaths:
    env = os.environ if env is None else env
    return SystemPipelinePaths(
        eval_path=_resolve_path(
            env,
            "KD_AGENT_SYSTEM_EVAL_PATH",
            PROJECT_ROOT / "data" / "eval" / "baseline_smoke_questions.jsonl",
        ),
        output_path=_resolve_path(
            env,
            "KD_AGENT_SYSTEM_OUTPUT_PATH",
            PROJECT_ROOT / "outputs" / "system" / "system_results.jsonl",
        ),
        report_path=_resolve_path(
            env,
            "KD_AGENT_SYSTEM_REPORT_PATH",
            PROJECT_ROOT / "reports" / "system_pipeline_smoke_test.md",
        ),
    )
