# 高效自动化知识蒸馏与智能体生成管线

本项目构建一套本地可运行的知识结构化蒸馏与智能体生成管线，将教材/讲义等资料解析为可检索、可引用、可评测的领域智能体配置。当前实现聚焦计算机学科，并已支持中文扫描教材 OCR 与英文 PDF 文本教材的双语联合检索评测。

## 当前状态

- `baseline`：LangChain + 标准 RAG + Qwen-8B-Instruct，用作对比基线。
- `src/`：早期正式系统链路，包含 PDF 解析、文本清洗分块、Chroma 索引和系统 RAG runner。
- `kd_agent/`：轻量、可离线运行的正式交付管线，包含解析、语义分块、本地 TF-IDF 检索、上下文压缩、引用约束回答和评测报告生成。
- `scripts/13_run_bilingual_raw_pdf_eval.py`：双语 raw PDF 评测脚本，可把中文扫描教材 OCR 片段和英文教材文本 chunk 放入同一个索引。

## 最新双语评测

数据源位于实际运行目录：`/root/autodl-tmp/kd_agent_pipeline/data/raw/cs/`。

- 中文教材：`cs-cn.pdf`，扫描版，使用 Tesseract `chi_sim+eng` 对代表页 OCR。
- 英文教材：`cs-eg.pdf`，使用原系统清洗后的高质量文本 chunk。
- 要求：中文问题必须中文回答，英文问题必须英文回答；同一检索索引同时包含两本教材，并通过术语扩展支持跨语言检索。

最新报告：`reports/bilingual_cs_evaluation.md`

| 指标 | 数值 |
| --- | --- |
| 中文 OCR chunk | 54 |
| 英文文本 chunk | 1572 |
| 总 chunk | 1626 |
| 测试问题数 | 8 |
| 回答语言匹配率 | 100.00% |
| 平均答案关键词召回 | 70.83% |
| 无引用生成/幻觉率 | 0.00% |
| 平均总 Token | 543.25 |

## 快速运行

运行轻量样例闭环：

```bash
bash run.sh
```

运行双语 raw PDF 评测：

```bash
PYTHONPATH=$(pwd) /root/autodl-tmp/kd_agent_pipeline/envs/kd_agent/bin/python scripts/13_run_bilingual_raw_pdf_eval.py
```

首次运行双语评测需要系统中有 Tesseract 和中英文语言包：

```bash
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng
```

## 目录结构

```text
kd_agent_pipeline/
├── agent_configs/                  # 生成/维护的智能体配置
├── configs/                        # Ollama Modelfile 与 baseline/system 配置
├── data/
│   ├── eval/                       # 评测问题与 ground truth/关键词标注
│   └── sample/                     # 可提交的小型样例资料
├── docs/                           # 架构和目录说明
├── kd_agent/                       # 轻量正式交付管线源码
├── reports/                        # 可提交的评测与复现实验报告
├── scripts/                        # baseline、system、kd_agent 自动化脚本
├── src/                            # 早期正式系统 PDF/RAG 组件
├── tests/                          # 单元测试
├── run.sh                          # Linux/macOS 一键运行轻量闭环
├── deploy.ps1                      # Windows 一键运行轻量闭环
├── requirements.txt                # 轻量正式系统依赖
└── requirements-baseline.txt       # baseline 依赖
```

详细目录职责见：`docs/project_structure.md`。

## 主要命令

轻量正式系统：

```bash
python scripts/10_build_kd_agent_index.py
python scripts/11_run_kd_agent_eval.py
python scripts/12_generate_kd_agent_report.py
```

Baseline 复现：

```bash
bash scripts/run_baseline.sh
```

早期 system 链路：

```bash
bash scripts/run_parser.sh
bash scripts/run_chunker.sh
bash scripts/run_system_indexer.sh
```

双语 raw PDF 评测：

```bash
PYTHONPATH=$(pwd) /root/autodl-tmp/kd_agent_pipeline/envs/kd_agent/bin/python scripts/13_run_bilingual_raw_pdf_eval.py
```

## 报告索引

- `reports/baseline_reproduction.md`：baseline 复现实验记录。
- `reports/system_pipeline_smoke_test.md`：早期 system 链路 smoke test。
- `reports/baseline_vs_system_comparison.md`：baseline 与 system 对比。
- `reports/kd_agent_evaluation.md`：轻量 `kd_agent` 样例评测。
- `reports/raw_pdf_clean_cs_evaluation.md`：英文 raw PDF 清洗 chunk 评测。
- `reports/bilingual_cs_evaluation.md`：中文 OCR + 英文文本双语联合评测。

## Git 与生成物约定

仓库只保留源码、配置、样例数据、评测题和 Markdown 报告。以下内容由脚本生成，不提交：

- `data/raw/`：原始教材、音频、图片等大文件。
- `data/processed/`：OCR 缓存、解析页、临时 chunk。
- `data/indexes/`：检索索引。
- `outputs/`：JSONL/JSON/CSV 运行输出。
- `__pycache__/`、`.pytest_cache/`、模型权重和缓存目录。

## Ollama 集成

- baseline：`configs/Modelfile.baseline`
- early system：`configs/Modelfile.system`
- kd_agent：`configs/Modelfile.kd_agent`

默认 GGUF 权重不提交，需要放在本地 `models/gguf/` 后再执行对应 build 脚本。
