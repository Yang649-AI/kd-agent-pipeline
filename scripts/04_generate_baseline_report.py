import json
from pathlib import Path
import sys
from datetime import datetime


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from common.paths import PROJECT_ROOT


METRIC_PATH = PROJECT_ROOT / "outputs" / "baseline" / "baseline_metrics.json"
RESULT_PATH = PROJECT_ROOT / "outputs" / "baseline" / "baseline_results.jsonl"
REPORT_PATH = PROJECT_ROOT / "reports" / "baseline_reproduction.md"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main():
    metrics = load_json(METRIC_PATH)
    results = load_jsonl(RESULT_PATH)

    lines = []
    lines.append("# Baseline 复现实验记录")
    lines.append("")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## 1. Baseline 名称")
    lines.append("")
    lines.append("LangChain + 标准 RAG + Qwen-8B-Instruct")
    lines.append("")
    lines.append("## 2. 实际运行模型")
    lines.append("")
    lines.append(f"- 运行框架：Ollama")
    lines.append(f"- 实际模型名称：{metrics.get('model')}")
    lines.append("- 模型来源：Qwen3-8B-Q4_K_M.gguf 通过 Ollama Modelfile 构建")
    lines.append("- 模型用途：用于复现 Qwen-8B-Instruct 对比基线")
    lines.append("")
    lines.append("## 3. RAG 配置")
    lines.append("")
    lines.append(f"- 向量库：Chroma")
    lines.append(f"- Embedding 模型：BAAI/bge-small-zh-v1.5")
    lines.append(f"- 分块方式：RecursiveCharacterTextSplitter 固定长度切分")
    lines.append(f"- chunk_size：{metrics.get('chunk_size')}")
    lines.append(f"- chunk_overlap：{metrics.get('chunk_overlap')}")
    lines.append(f"- top_k：{metrics.get('top_k')}")
    lines.append("- temperature：0")
    lines.append("- num_ctx：4096")
    lines.append("")
    lines.append("## 4. 未启用的优化项")
    lines.append("")
    lines.append("- 未启用自适应分块")
    lines.append("- 未启用重排序 rerank")
    lines.append("- 未启用上下文压缩")
    lines.append("- 未启用动态 Top-K")
    lines.append("- 未启用 LoRA 微调")
    lines.append("")
    lines.append("## 5. 当前 smoke test 指标")
    lines.append("")
    lines.append(f"- 测试问题数：{metrics.get('num_questions')}")
    lines.append(f"- 平均延迟：{metrics.get('avg_latency_sec'):.2f} s")
    lines.append(f"- 最大延迟：{metrics.get('max_latency_sec'):.2f} s")
    lines.append(f"- 最小延迟：{metrics.get('min_latency_sec'):.2f} s")
    lines.append(f"- 平均输入 Token：{metrics.get('avg_input_tokens'):.2f}")
    lines.append(f"- 平均输出 Token：{metrics.get('avg_output_tokens'):.2f}")
    lines.append(f"- 平均总 Token：{metrics.get('avg_total_tokens'):.2f}")
    lines.append(f"- 总 Token：{metrics.get('sum_total_tokens')}")
    lines.append("")
    lines.append("## 6. Smoke test 问答样例")
    lines.append("")

    for item in results:
        lines.append(f"### {item.get('id')}")
        lines.append("")
        lines.append(f"问题：{item.get('question')}")
        lines.append("")
        answer = item.get("answer", "").replace("\n", " ")
        lines.append(f"回答摘要：{answer[:500]}")
        lines.append("")
        lines.append("检索来源：")
        for i, doc in enumerate(item.get("retrieved", []), start=1):
            lines.append(
                f"- [{i}] {doc.get('source_file')}，page={doc.get('page')}"
            )
        lines.append("")

    lines.append("## 7. 当前数据集说明")
    lines.append("")
    lines.append("- `cs-eg.pdf` 可以被 PyMuPDF 正常抽取文字，并已成功构建 baseline 向量库。")
    lines.append("- `cs-cn.pdf` 为扫描版或图片版 PDF，PyMuPDF 抽取前 10 页文字长度均为 0，因此未进入当前 baseline 向量库。")
    lines.append("- 当前结果用于验证 baseline 工程链路，不作为最终三学科正式评测结果。")
    lines.append("")
    lines.append("## 8. 后续工作")
    lines.append("")
    lines.append("- 准备可抽取文字的中文资料，或在正式系统中加入 OCR 解析流程。")
    lines.append("- 构建正式评测集，补充标准答案、证据页码和 Hit@5 评价。")
    lines.append("- 与后续优化系统进行 Token 消耗、延迟、Hit@5 和无引用生成比例对比。")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Baseline report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
