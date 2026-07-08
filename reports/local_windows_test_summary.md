# 本地 Windows 测试摘要

生成时间：2026-07-06

## 1. Power PMAC PDF 处理结果

- 原始 chunk 数：4091
- 入索引高质量 chunk 数：4055
- OCR todo 页：{"Power PMAC Software Reference Manual.pdf": 1}

## 2. kd_agent 默认评测结果

- 测试问题数：6
- 平均答案关键词召回：100.00%
- 无引用生成/幻觉率：0.00%
- 平均延迟：0.0006 s
- 平均总 Token：368.50
- 平均上下文压缩比例：68.52%

## 3. 说明

- `Power PMAC Software Reference Manual.pdf` 已完成分页解析、结构化分块和 system Chroma 索引构建。
- `kd_agent` 默认评测跑的是 `data/sample/cs/` 与 `data/eval/cs_eval_questions.jsonl`，不是 `Power PMAC` 手册本身。
- 当前正式评测报告见 `reports/kd_agent_evaluation.md`。
