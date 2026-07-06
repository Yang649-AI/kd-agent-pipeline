# 高效自动化知识蒸馏与智能体生成管线

本项目面向多学科资料的本地垂直领域智能体生成任务，构建从资料解析、知识结构化封装、检索增强问答、引用溯源到 Ollama 兼容配置的一体化管线。

当前仓库包含两条链路：

- `baseline`：LangChain + 标准 RAG + Qwen-8B-Instruct，用于对比复现。
- `kd_agent`：本项目实现的自适应知识蒸馏与引用约束智能体管线。

按当前需求，本轮先使用计算机单学科数据集完成闭环评测，暂不做医学、法学三学科验证。

## 已完成内容

- 多格式解析框架：Markdown/TXT/JSONL/PDF/EPUB，图片和音频保留本地 OCR/ASR 接入点。
- 自适应语义分块：保留标题层级、句边界、来源、模态、关键词和页码元数据。
- 结构化知识蒸馏：生成轻量 chunk JSON 索引。
- 本地检索智能体：TF-IDF/关键词检索、问题相关上下文压缩、Citation Grounding。
- Ollama 兼容配置：`configs/Modelfile.kd_agent` 与 `agent_configs/cs_agent.json`。
- 计算机单学科样例数据集与 ground truth：`data/sample/cs/`、`data/eval/cs_eval_questions.jsonl`。
- 自动评测与报告：Hit@5、答案关键词命中率、无引用生成率、延迟、token 消耗。
- 一键脚本：Linux/macOS `run.sh`，Windows `deploy.ps1`。

## 快速运行

Linux/macOS：

```bash
cd /path/to/kd-agent-pipeline
bash run.sh
```

Windows + Conda：

```powershell
cd D:\program\code\Python\kd-agent-pipeline
conda activate kd-agent-pipeline-gpu
$env:KD_AGENT_PROJECT_ROOT="D:\program\code\Python\kd-agent-pipeline"
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

运行后会生成：

- `data/indexes/kd_agent_cs/index.json`：结构化知识索引
- `agent_configs/cs_agent.json`：标准化智能体配置
- `outputs/kd_agent/cs_results.jsonl`：逐题评测结果
- `outputs/kd_agent/cs_metrics.json`：汇总指标
- `reports/kd_agent_evaluation.md`：评估报告

## 当前实测指标

最近一次本地运行结果：

| 指标 | 数值 |
| --- | --- |
| 学科 | 计算机 |
| 测试问题数 | 6 |
| Hit@5 | 100.00% |
| 答案关键词命中率 | 100.00% |
| 无引用生成/幻觉率 | 0.00% |
| 平均总 Token | 368.50 |
| 平均上下文压缩比例 | 68.52% |

完整报告见 `reports/kd_agent_evaluation.md`。

## 目录结构

```text
kd_agent_pipeline/
├── agent_configs/                  # 生成的智能体配置
├── configs/                        # Ollama Modelfile 与 baseline 配置
├── data/
│   ├── eval/                       # 评测问题与 ground truth
│   └── sample/cs/                  # 当前计算机样例数据集
├── docs/                           # 架构与技术文档
├── kd_agent/                       # 正式系统源码
├── reports/                        # baseline 与系统评估报告
├── scripts/                        # baseline 与 kd_agent 自动化脚本
├── tests/                          # 单元测试
├── run.sh                          # Linux/macOS 一键运行
├── deploy.ps1                      # Windows 一键运行
├── requirements.txt                # 正式系统最小依赖
└── requirements-baseline.txt       # baseline 依赖
```

## 正式系统命令

```bash
python scripts/10_build_kd_agent_index.py
python scripts/11_run_kd_agent_eval.py
python scripts/12_generate_kd_agent_report.py
```

也可以直接运行：

```bash
bash scripts/run_kd_agent.sh
```

## Baseline 复现

baseline 保留原始设计：LangChain + Chroma + BAAI/bge-small-zh-v1.5 + Ollama Qwen-8B-Instruct。

本地环境准备：

```bash
cd /path/to/kd-agent-pipeline
source setup_paths.sh
conda activate "${KD_AGENT_CONDA_ENV:-kd-agent-pipeline-gpu}"
python -m pip install -r requirements-baseline.txt
```

Windows + Conda 可使用：

```powershell
cd D:\program\code\Python\kd-agent-pipeline
conda activate kd-agent-pipeline-gpu
$env:KD_AGENT_PROJECT_ROOT="D:\program\code\Python\kd-agent-pipeline"
```

运行 baseline：

```bash
python scripts/01_build_baseline_index.py
python scripts/02_run_baseline.py
python scripts/03_calc_baseline_metrics.py
python scripts/04_generate_baseline_report.py
```

也可以直接运行：

```bash
bash scripts/run_baseline.sh
```

注意：baseline 依赖较重，需要本地已有模型、Ollama、embedding 模型缓存或网络下载能力。

当前 smoke test 主要基于 `cs-eg.pdf` 完成，该 PDF 可被 PyMuPDF 正常抽取文字。

`cs-cn.pdf` 为扫描版或图片版 PDF，PyMuPDF 抽取前 10 页文字长度均为 0，因此未进入当前 baseline 向量库。

## Ollama 集成

正式系统的 Ollama 配置位于：

```text
configs/Modelfile.kd_agent
```

默认指向：

```text
models/gguf/Qwen3-VL-8B-Instruct-Q4_K_M.gguf
```

若实际权重文件名不同，修改 `FROM` 路径后执行：

```bash
ollama create qwen3-vl-8b-kd-agent -f configs/Modelfile.kd_agent
```

当前 `kd_agent` 在无 Ollama、无 GPU 环境下也能用抽取式引用回答完成评测闭环；接入 Ollama 后建议保留检索、上下文压缩和引用守卫。

## 文档

- 架构设计：`docs/architecture.md`
- 系统评估报告：`reports/kd_agent_evaluation.md`
- baseline 复现实验：`reports/baseline_reproduction.md`

## 后续扩展

- 将 `data/sample/cs/` 替换为正式 >=100 页计算机教材或讲义。
- 新增 `data/sample/medicine`、`data/sample/law` 与对应 eval JSONL 后即可扩展三学科评测。
- 接入本地 OCR/ASR：PaddleOCR/Tesseract、whisper.cpp 或 faster-whisper。
- 接入 Ollama 生成式回答，并复测 token、延迟、Hit@5 和无引用生成率。
