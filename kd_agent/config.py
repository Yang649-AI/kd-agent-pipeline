from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def project_root() -> Path:
    return Path(os.environ.get("PROJECT_ROOT", Path.cwd())).resolve()


@dataclass(frozen=True)
class PipelineConfig:
    project_root: Path
    raw_dirs: tuple[Path, ...]
    eval_path: Path
    index_path: Path
    results_path: Path
    metrics_path: Path
    report_path: Path
    agent_config_path: Path
    discipline: str = "cs"
    chunk_target_tokens: int = 360
    chunk_min_tokens: int = 120
    chunk_overlap_tokens: int = 40
    top_k: int = 5
    compressed_context_tokens: int = 900
    baseline_context_tokens: int = 1800


def default_config() -> PipelineConfig:
    root = project_root()
    return PipelineConfig(
        project_root=root,
        raw_dirs=(root / "data" / "sample" / "cs", root / "data" / "raw" / "cs"),
        eval_path=root / "data" / "eval" / "cs_eval_questions.jsonl",
        index_path=root / "data" / "indexes" / "kd_agent_cs" / "index.json",
        results_path=root / "outputs" / "kd_agent" / "cs_results.jsonl",
        metrics_path=root / "outputs" / "kd_agent" / "cs_metrics.json",
        report_path=root / "reports" / "kd_agent_evaluation.md",
        agent_config_path=root / "agent_configs" / "cs_agent.json",
    )
