from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import PipelineConfig
from .evaluation import load_jsonl
from .indexing import load_index


def _load_optional_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def generate_report(config: PipelineConfig) -> None:
    metrics = _load_optional_json(config.metrics_path) or {}
    baseline_metrics = _load_optional_json(config.project_root / "outputs" / "baseline" / "baseline_metrics.json")
    results = load_jsonl(config.results_path) if config.results_path.exists() else []
    index = load_index(config.index_path)

    baseline_avg_tokens = (baseline_metrics or {}).get("avg_total_tokens")
    system_avg_tokens = metrics.get("avg_total_tokens")
    if baseline_avg_tokens and system_avg_tokens:
        token_ratio = system_avg_tokens / baseline_avg_tokens
        token_line = f"- 平均总 Token 比例：{token_ratio:.2%}（系统 / baseline）"
    else:
        token_line = "- 平均总 Token 比例：baseline 尚未在当前环境生成，报告先记录系统实测值。"

    lines: list[str] = []
    lines.append("# 高效自动化知识蒸馏与智能体生成管线评估报告")
    lines.append("")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## 1. 评测范围")
    lines.append("")
    lines.append("本轮按用户要求仅使用计算机学科数据集进行闭环验证，暂不做医学、法学三学科扩展。")
    lines.append("数据集位于 `data/sample/cs/` 与 `data/eval/cs_eval_questions.jsonl`，包含操作系统、体系结构、异常控制流、Amdahl 定律、RAG 等主题的 ground truth 标注。")
    lines.append("")
    lines.append("## 2. 系统方案")
    lines.append("")
    lines.append("- 多格式解析：支持 Markdown/TXT/JSONL/PDF/EPUB，并为图片、音频保留本地 OCR/ASR 降级占位链路。")
    lines.append("- 自适应分块：优先保留标题层级与语义句边界，记录学科、来源、模态、关键词和页码元数据。")
    lines.append("- 结构化蒸馏：将原始资料封装为轻量 chunk JSON 索引，不做权重蒸馏。")
    lines.append("- 检索增强：使用本地 TF-IDF/关键词评分，避免在无网络或无 GPU 环境下阻塞。")
    lines.append("- 上下文压缩：按问题筛选证据句，控制进入生成端的 token 预算。")
    lines.append("- Citation Grounding：答案必须带 `[Sx]` 引用锚点，无依据时输出 `未找到参考资料`。")
    lines.append("")
    lines.append("## 3. 索引统计")
    lines.append("")
    lines.append(f"- chunk 数：{len(index.chunks)}")
    lines.append(f"- 平均 chunk token：{sum(c.token_count for c in index.chunks) / max(1, len(index.chunks)):.2f}")
    lines.append(f"- 最大 chunk token：{max((c.token_count for c in index.chunks), default=0)}")
    lines.append("")
    lines.append("## 4. 指标结果")
    lines.append("")
    lines.append(f"- 测试问题数：{metrics.get('num_questions', 0)}")
    lines.append(f"- Hit@5：{metrics.get('hit_at_5', 0):.2%}")
    lines.append(f"- 答案关键词命中率：{metrics.get('answer_term_accuracy', 0):.2%}")
    lines.append(f"- 无引用生成/幻觉率：{metrics.get('hallucination_rate_no_citation', 0):.2%}")
    lines.append(f"- 平均延迟：{metrics.get('avg_latency_sec', 0):.4f} s")
    lines.append(f"- 平均输入 Token：{metrics.get('avg_input_tokens', 0):.2f}")
    lines.append(f"- 平均输出 Token：{metrics.get('avg_output_tokens', 0):.2f}")
    lines.append(f"- 平均总 Token：{metrics.get('avg_total_tokens', 0):.2f}")
    lines.append(f"- 平均上下文压缩比例：{metrics.get('avg_context_compression_ratio', 0):.2%}")
    lines.append(token_line)
    lines.append("")
    lines.append("## 5. 消融说明")
    lines.append("")
    lines.append("| 设置 | 预期影响 | 当前实现记录 |")
    lines.append("| --- | --- | --- |")
    lines.append("| 关闭上下文压缩 | Token 上升，可能提高少量召回 | 当前报告记录压缩比例，可用 `compressed_context_tokens` 调大模拟 |")
    lines.append("| 固定长度分块 | 标题/证据边界破碎 | baseline 使用固定 chunk_size=1000 作为对照 |")
    lines.append("| 关闭引用约束 | 幻觉率上升 | 当前 agent 默认拒绝无依据回答 |")
    lines.append("| Q4/Q5 量化切换 | 显存、延迟、质量权衡 | Ollama Modelfile 已提供 Q4 路径，后续替换 GGUF 即可复测 |")
    lines.append("")
    lines.append("## 6. 样例结果")
    lines.append("")
    for item in results:
        lines.append(f"### {item.get('id')}")
        lines.append("")
        lines.append(f"问题：{item.get('question')}")
        lines.append("")
        lines.append(f"回答：{item.get('answer')}")
        lines.append("")
        lines.append(f"Hit@5：{item.get('hit_at_5')}，引用：{', '.join(item.get('citations', [])) or '无'}")
        lines.append("")
    lines.append("## 7. 已知边界与后续迭代")
    lines.append("")
    lines.append("- 当前补齐的是计算机单学科小型可复现数据集，不代表最终 ≥100 页正式教材评测规模。")
    lines.append("- 图片与音频路径已纳入解析框架，但正式 OCR/ASR 需在有依赖时接入 PaddleOCR、Tesseract、whisper.cpp 或 faster-whisper。")
    lines.append("- 若接入 Ollama 生成模型，建议保持本地检索和引用守卫不变，只替换 `grounded_extractive_answer` 的生成阶段。")
    lines.append("- 三学科扩展时只需新增 `data/sample/{medicine,law}` 与对应 eval JSONL，再按同一脚本运行。")
    lines.append("")
    config.report_path.parent.mkdir(parents=True, exist_ok=True)
    config.report_path.write_text("\n".join(lines), encoding="utf-8")
