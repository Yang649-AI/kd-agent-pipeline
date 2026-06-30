import json
from pathlib import Path
import pandas as pd


RESULT_PATH = Path("outputs/baseline/baseline_results.jsonl")
METRIC_PATH = Path("outputs/baseline/baseline_metrics.json")
CSV_PATH = Path("outputs/baseline/baseline_results_summary.csv")


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main():
    results = load_jsonl(RESULT_PATH)

    if not results:
        raise RuntimeError(f"No results found in {RESULT_PATH}")

    rows = []
    for item in results:
        rows.append({
            "id": item.get("id"),
            "discipline": item.get("discipline"),
            "question": item.get("question"),
            "latency_sec": item.get("latency_sec", 0),
            "input_tokens": item.get("input_tokens", 0),
            "output_tokens": item.get("output_tokens", 0),
            "total_tokens": item.get("total_tokens", 0),
            "top_k": item.get("top_k"),
            "model": item.get("model"),
            "chunk_size": item.get("chunk_size"),
            "chunk_overlap": item.get("chunk_overlap"),
        })

    df = pd.DataFrame(rows)

    metrics = {
        "baseline_name": "LangChain + 标准 RAG + Qwen-8B-Instruct",
        "num_questions": int(len(df)),
        "model": str(df["model"].iloc[0]),
        "top_k": int(df["top_k"].iloc[0]),
        "chunk_size": int(df["chunk_size"].iloc[0]),
        "chunk_overlap": int(df["chunk_overlap"].iloc[0]),
        "avg_latency_sec": float(df["latency_sec"].mean()),
        "max_latency_sec": float(df["latency_sec"].max()),
        "min_latency_sec": float(df["latency_sec"].min()),
        "avg_input_tokens": float(df["input_tokens"].mean()),
        "avg_output_tokens": float(df["output_tokens"].mean()),
        "avg_total_tokens": float(df["total_tokens"].mean()),
        "sum_total_tokens": int(df["total_tokens"].sum()),
        "adaptive_chunking": False,
        "rerank": False,
        "context_compression": False,
        "dynamic_top_k": False,
        "lora": False,
    }

    METRIC_PATH.parent.mkdir(parents=True, exist_ok=True)

    METRIC_PATH.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"\nSaved metrics to: {METRIC_PATH}")
    print(f"Saved summary CSV to: {CSV_PATH}")


if __name__ == "__main__":
    main()
