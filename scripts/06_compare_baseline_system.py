import json
from pathlib import Path
from statistics import mean


PROJECT_ROOT = Path("/root/autodl-tmp/kd_agent_pipeline")

BASELINE_RESULT_PATH = PROJECT_ROOT / "outputs" / "baseline" / "baseline_results.jsonl"
SYSTEM_RESULT_PATH = PROJECT_ROOT / "outputs" / "system" / "system_results.jsonl"
REPORT_PATH = PROJECT_ROOT / "reports" / "baseline_vs_system_comparison.md"


def load_jsonl(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    return records


def is_not_found_answer(answer: str) -> bool:
    if not answer:
        return True

    text = answer.strip().lower()

    patterns = [
        "未找到参考资料",
        "no supporting reference was found",
        "not found",
        "insufficient context",
        "cannot answer",
    ]

    return any(p in text for p in patterns)


def get_latency(item: dict):
    for key in ["latency_seconds", "latency_s", "latency", "elapsed_seconds"]:
        if key in item and isinstance(item[key], (int, float)):
            return item[key]
    return None


def get_token_count(item: dict):
    for key in ["total_tokens", "token_count", "tokens"]:
        if key in item and isinstance(item[key], (int, float)):
            return item[key]
    return None


def summarize(records):
    total = len(records)
    answered = 0
    not_found = 0
    retrieved_counts = []
    latencies = []
    token_counts = []

    for item in records:
        answer = item.get("answer", "")
        if is_not_found_answer(answer):
            not_found += 1
        else:
            answered += 1

        retrieved = item.get("retrieved", [])
        if isinstance(retrieved, list):
            retrieved_counts.append(len(retrieved))

        latency = get_latency(item)
        if latency is not None:
            latencies.append(latency)

        tokens = get_token_count(item)
        if tokens is not None:
            token_counts.append(tokens)

    return {
        "total": total,
        "answered": answered,
        "not_found": not_found,
        "answer_rate": answered / total if total else 0.0,
        "avg_retrieved": mean(retrieved_counts) if retrieved_counts else 0.0,
        "avg_latency": mean(latencies) if latencies else None,
        "avg_tokens": mean(token_counts) if token_counts else None,
    }


def short_answer(answer: str, max_len: int = 180) -> str:
    answer = answer.replace("\n", " ").replace("|", "\\|").strip()
    if len(answer) > max_len:
        return answer[:max_len] + "..."
    return answer


def main():
    baseline = load_jsonl(BASELINE_RESULT_PATH)
    system = load_jsonl(SYSTEM_RESULT_PATH)

    baseline_by_id = {item.get("id"): item for item in baseline}
    system_by_id = {item.get("id"): item for item in system}

    common_ids = sorted(set(baseline_by_id.keys()) & set(system_by_id.keys()))

    baseline_summary = summarize(baseline)
    system_summary = summarize(system)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Baseline 与 System 管线对比报告")
    lines.append("")
    lines.append("## 1. 报告目的")
    lines.append("")
    lines.append(
        "本报告用于对比 baseline 管线与当前正式 system 管线在同一组 smoke test 问题上的运行结果。"
        "对比内容包括问答覆盖情况、检索片段数量、回答状态以及系统管线相对于 baseline 的结构化改进。"
    )
    lines.append("")
    lines.append("## 2. 对比对象")
    lines.append("")
    lines.append("| 对比项 | Baseline 管线 | 当前 System 验证管线 |")
    lines.append("|---|---|---|")
    lines.append("| 角色 | baseline 复现 | 正式系统管线 smoke test 验证 |")
    lines.append("| 配置文件 | `configs/baseline_config.yaml` | `configs/system_config.yaml` |")
    lines.append("| 文档解析 | LangChain 默认 PDF 加载 | `src/parser/parse_pdf_pages.py` 分页解析 |")
    lines.append("| 文本分块 | 标准文本切分 | 带质量标注的结构化分块 |")
    lines.append("| 向量库 | Chroma | Chroma |")
    lines.append("| 问答模型 | Qwen 8B 级 Ollama 验证模型 | 临时 Ollama 验证模型 |")
    lines.append("| 正式目标模型 | 不适用 | Qwen3-VL-8B |")
    lines.append("| OCR / 多模态处理 | 未覆盖 | 已记录 OCR todo，后续接入多模态解析 |")
    lines.append("")
    lines.append("## 3. 总体指标对比")
    lines.append("")
    lines.append("| 指标 | Baseline | System 验证管线 |")
    lines.append("|---|---:|---:|")
    lines.append(f"| 问题总数 | {baseline_summary['total']} | {system_summary['total']} |")
    lines.append(f"| 成功回答数 | {baseline_summary['answered']} | {system_summary['answered']} |")
    lines.append(f"| 未找到参考资料数 | {baseline_summary['not_found']} | {system_summary['not_found']} |")
    lines.append(f"| 回答覆盖率 | {baseline_summary['answer_rate']:.2%} | {system_summary['answer_rate']:.2%} |")
    lines.append(f"| 平均检索片段数 | {baseline_summary['avg_retrieved']:.2f} | {system_summary['avg_retrieved']:.2f} |")

    if baseline_summary["avg_latency"] is not None or system_summary["avg_latency"] is not None:
        b = "N/A" if baseline_summary["avg_latency"] is None else f"{baseline_summary['avg_latency']:.2f}"
        s = "N/A" if system_summary["avg_latency"] is None else f"{system_summary['avg_latency']:.2f}"
        lines.append(f"| 平均响应时间 / s | {b} | {s} |")

    if baseline_summary["avg_tokens"] is not None or system_summary["avg_tokens"] is not None:
        b = "N/A" if baseline_summary["avg_tokens"] is None else f"{baseline_summary['avg_tokens']:.2f}"
        s = "N/A" if system_summary["avg_tokens"] is None else f"{system_summary['avg_tokens']:.2f}"
        lines.append(f"| 平均 token 数 | {b} | {s} |")

    lines.append("")
    lines.append("## 4. 单问题结果对比")
    lines.append("")
    lines.append("| ID | 问题 | Baseline 状态 | System 状态 | Baseline 回答预览 | System 回答预览 |")
    lines.append("|---|---|---|---|---|---|")

    for qid in common_ids:
        b_item = baseline_by_id[qid]
        s_item = system_by_id[qid]

        question = b_item.get("question", "").replace("|", "\\|")
        b_answer = b_item.get("answer", "")
        s_answer = s_item.get("answer", "")

        b_status = "未找到参考资料" if is_not_found_answer(b_answer) else "已回答"
        s_status = "未找到参考资料" if is_not_found_answer(s_answer) else "已回答"

        lines.append(
            f"| {qid} | {question} | {b_status} | {s_status} | "
            f"{short_answer(b_answer)} | {short_answer(s_answer)} |"
        )

    lines.append("")
    lines.append("## 5. System 管线相对于 Baseline 的改进点")
    lines.append("")
    lines.append("当前 system 管线并不是简单复刻 baseline，而是在 baseline 基础上增加了以下工程化能力：")
    lines.append("")
    lines.append("1. **分页级 PDF 解析**：将 PDF 按页解析并保留页码、来源文件、学科类别和引用锚点。")
    lines.append("2. **结构化知识块生成**：在分块阶段保留 chunk_id、source_file、page、citation_anchor 等元数据。")
    lines.append("3. **知识块质量标注**：为每个 chunk 增加 `quality_score`、`is_low_quality`、`quality_reasons` 和 `content_role` 字段。")
    lines.append("4. **OCR 待处理页记录**：对扫描页或图片页生成 `ocr_todo_pages.jsonl`，为后续 OCR 或多模态解析预留入口。")
    lines.append("5. **正式系统配置分离**：通过 `configs/system_config.yaml` 明确正式系统目标模型为 `Qwen3-VL-8B`。")
    lines.append("6. **Ollama 兼容部署模板**：通过 `configs/Modelfile.system` 和 `scripts/build_system_ollama_model.sh` 预留正式系统模型构建流程。")
    lines.append("")
    lines.append("## 6. 当前阶段说明")
    lines.append("")
    lines.append(
        "当前 system RAG runner 仍属于管线验证阶段，使用临时 Ollama 文本模型验证解析、分块、索引、检索、问答与引用输出流程。"
        "正式系统目标模型已在 `configs/system_config.yaml` 中明确为 `Qwen3-VL-8B`，后续需要继续接入 OCR、多模态页面解析和 LoRA 微调流程。"
    )
    lines.append("")
    lines.append("本报告属于 smoke test 对比报告，不等同于最终性能评测报告。后续应扩展更大规模测试集，并加入引用正确性、答案忠实性、幻觉率、响应延迟和多模态文档覆盖率等指标。")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"对比报告已生成: {REPORT_PATH}")
    print(f"共同问题数: {len(common_ids)}")
    print(f"Baseline 已回答: {baseline_summary['answered']} / {baseline_summary['total']}")
    print(f"System 已回答: {system_summary['answered']} / {system_summary['total']}")


if __name__ == "__main__":
    main()
