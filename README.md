# 高效自动化知识蒸馏与智能体生成管线

本项目面向多学科资料的本地垂直领域智能体生成任务，目标是构建从多模态资料输入、知识结构化封装、RAG 检索增强问答到 Ollama 本地部署的一体化工程管线。

当前仓库已完成对比基线的最小复现流程：

**LangChain + 标准 RAG + Qwen-8B-Instruct**

其中，Qwen-8B-Instruct 基线通过本地 GGUF 量化权重与 Ollama Modelfile 构建得到，实际运行模型名称为：

`qwen-8b-instruct-baseline`

## 1. 当前已完成内容

- 搭建项目目录结构
- 配置 Conda 环境与缓存路径
- 完成 `.gitignore` 配置，避免上传模型、环境、缓存和原始数据
- 上传计算机领域测试 PDF
- 构建 LangChain 标准 RAG baseline 向量库
- 通过 GGUF + Modelfile 构建 Ollama 本地 baseline 模型
- 运行 baseline smoke test
- 生成 baseline 指标统计文件
- 生成 baseline 复现实验记录

## 2. Baseline 配置

| 项目 | 配置 |
| --- | --- |
| Baseline 名称 | LangChain + 标准 RAG + Qwen-8B-Instruct |
| RAG 框架 | LangChain |
| 向量库 | Chroma |
| Embedding 模型 | BAAI/bge-small-zh-v1.5 |
| 分块方式 | RecursiveCharacterTextSplitter 固定长度切分 |
| chunk_size | 1000 |
| chunk_overlap | 200 |
| top_k | 5 |
| 模型运行框架 | Ollama |
| 实际模型名称 | qwen-8b-instruct-baseline |
| temperature | 0 |
| num_ctx | 4096 |

Baseline 不启用以下优化：

- 自适应分块
- rerank 重排序
- 上下文压缩
- 动态 Top-K
- LoRA 微调

## 3. 当前目录结构

```text
kd_agent_pipeline/
├── configs/
│   ├── baseline_config.yaml
│   └── Modelfile.baseline
├── data/
│   └── eval/
│       └── baseline_smoke_questions.jsonl
├── reports/
│   └── baseline_reproduction.md
├── scripts/
│   ├── 01_build_baseline_index.py
│   ├── 02_run_baseline.py
│   ├── 03_calc_baseline_metrics.py
│   └── 04_generate_baseline_report.py
├── setup_paths.sh
├── requirements-baseline.txt
├── .gitignore
└── README.md

## 4. 环境准备

进入项目目录：

cd /root/autodl-tmp/kd_agent_pipeline

加载路径配置：

source setup_paths.sh

激活 Conda 环境：

conda activate /root/autodl-tmp/kd_agent_pipeline/envs/kd_agent

安装 baseline 依赖：

python -m pip install -r requirements-baseline.txt

## 5. Baseline 复现流程

构建 baseline 向量库：

python scripts/01_build_baseline_index.py

运行 baseline 问答：

python scripts/02_run_baseline.py

统计 baseline 指标：

python scripts/03_calc_baseline_metrics.py

生成 baseline 复现实验记录：

python scripts/04_generate_baseline_report.py

## 6. 当前测试数据说明

当前 smoke test 主要基于 cs-eg.pdf 完成，该 PDF 可被 PyMuPDF 正常抽取文字。

cs-cn.pdf 为扫描版或图片版 PDF，PyMuPDF 抽取前 10 页文字长度均为 0，因此未进入当前 baseline 向量库。该问题可作为后续正式系统加入 OCR 解析模块的改进依据。