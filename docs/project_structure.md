# 项目目录说明

本文件用于说明 `kd_agent_pipeline` 仓库整理后的目录职责，避免源码、数据、报告和运行生成物混在一起。

## 保留在 Git 中的内容

| 路径 | 职责 |
| --- | --- |
| `agent_configs/` | 标准化智能体配置，例如 system prompt、工具链和检索参数。 |
| `configs/` | Baseline、early system、kd_agent 的配置、Ollama Modelfile 和数据集 schema。 |
| `data/eval/` | 小型评测问题、关键词标注、语言标注等可复现评测入口。 |
| `data/sample/` | 可提交的小型样例资料，用于无 raw PDF 时跑通闭环。 |
| `docs/` | 架构设计、目录说明和后续可扩展文档。 |
| `kd_agent/` | 轻量正式管线源码：解析、分块、索引、回答、评测、报告。 |
| `reports/` | 可提交的 Markdown 评测报告和对比报告。 |
| `scripts/` | 自动化脚本，按编号区分 baseline、system、kd_agent 和双语评测流程。 |
| `src/` | 早期正式系统组件，保留 PDF 清洗、Chroma 索引和 RAG runner。 |
| `tests/` | 单元测试。 |

## 不保留在 Git 中的内容

这些内容会由运行脚本重新生成，已由 `.gitignore` 排除：

| 路径 | 原因 |
| --- | --- |
| `data/raw/` | 原始教材/音频/图片通常体积大，不进入仓库。 |
| `data/processed/` | OCR 缓存、解析页、临时 chunk，可复现生成。 |
| `data/indexes/` | 向量库或本地索引，可复现生成且体积可能较大。 |
| `outputs/` | JSONL/JSON/CSV 运行输出，可由报告脚本再生成。 |
| `logs/` | 本地服务和实验日志。 |
| `__pycache__/`、`.pytest_cache/` | Python 缓存。 |
| `models/`、`*.gguf` | 模型权重体积大，需本地准备。 |

## 脚本分组

- `01_*` 到 `04_*`：baseline 构建、问答、指标和报告。
- `05_*` 到 `06_*`：early system 报告和 baseline/system 对比。
- `10_*` 到 `12_*`：轻量 `kd_agent` 样例闭环。
- `13_run_bilingual_raw_pdf_eval.py`：中文 OCR + 英文 PDF 的双语联合评测。
- `run_*.sh`：对应流程的一键封装，包括 baseline、parser、chunker、system indexer、system RAG 和 kd_agent。

## 数据盘本地资产

服务器数据盘目录保留运行所需的大文件和缓存，例如 `data/raw/`、`models/`、`envs/`、`cache/`、`outputs/`。这些目录不上传 GitHub，但属于服务器项目运行资产，不应与源码交付物混淆。

## 报告取舍

保留最终或有对比价值的报告：baseline、system smoke、baseline vs system、kd_agent 样例、raw PDF clean、bilingual raw PDF。

已删除首轮未清洗 raw PDF 噪声报告，因为它被 `raw_pdf_clean_cs_evaluation.md` 和 `bilingual_cs_evaluation.md` 完全取代。
