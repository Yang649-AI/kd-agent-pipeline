# KD Agent Pipeline 交付实施计划

> **面向代理执行者：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，按任务逐项执行本计划。步骤使用复选框 `- [ ]` 语法进行跟踪。

**最后更新：** 2026-07-07

**目标：** 将 Windows 本地版 `kd-agent-pipeline` 从单文档 smoke 验证推进为可复现、可演示、可评测的 FY27 课题交付版本。

**当前主攻方向：** 先把 Power PMAC 这条 system 问答链路做稳，形成可手动提问、可生成报告、可复现实验指标的演示闭环；随后再扩展到三学科正式评测、OCR、多模态和最终交付文档。

**架构：** `local/windows-deploy` 只承担 Windows 本地运行适配，不直接污染 `main` 或 `feature/system-pipeline`。当前链路为：PDF 原始文件 -> 页面解析 -> 结构化 chunk -> Chroma 索引 -> Ollama/Qwen3 生成 -> JSONL 结果 -> Markdown 报告。

**技术栈：** Python 3.11、PyTorch 2.12.1、CUDA、PyMuPDF、LangChain、Chroma、BAAI/bge-small-zh-v1.5、Ollama 0.31.1、Qwen3 8B GGUF/Q4_K_M、PowerShell。

---

## 当前进度快照

当前仓库分支为：

```text
local/windows-deploy
```

已经完成：

- [x] Windows 本地路径适配：通过 `src/common/paths.py` 和 `KD_AGENT_PROJECT_ROOT` 支持本地项目根目录。
- [x] system 管线支持环境变量覆盖输入/输出路径：`KD_AGENT_SYSTEM_EVAL_PATH`、`KD_AGENT_SYSTEM_OUTPUT_PATH`、`KD_AGENT_SYSTEM_REPORT_PATH`。
- [x] Power PMAC PDF 已接入 system 管线。
- [x] Ollama 已安装并启动，本地 API `127.0.0.1:11434` 可访问。
- [x] 已拉取 `qwen3:8b`，并复制为项目默认模型名 `qwen-8b-instruct-baseline`。
- [x] system runner 已能使用 CUDA embedding 和 Ollama 生成。
- [x] 已解决直接调用 Python 时的 cuDNN 路径问题：需要 `conda activate` 或把 env 的 `Library\bin` 放到 PATH 前面。
- [x] 已增加 Ollama 不可用时的 `extractive_fallback` 降级。
- [x] 已清理 Qwen3 `/think`、`<think>...</think>` 等 reasoning 泄漏。
- [x] 已将 system prompt 调整为更稳的 grounding 规则，避免对无关 CS 问题用常识乱答。
- [x] 已生成 Power PMAC system 结果：`outputs/system/power_pmac_results.jsonl`。
- [x] 已生成 Power PMAC 报告：`reports/power_pmac_system_report.md`。
- [x] 已新增 Power PMAC 单问入口：`scripts/ask_power_pmac.ps1` 和 `src/agent/ask_system_once.py`。
- [x] 当前单元测试通过：`14` 个测试。

当前仍需注意：

- Power PMAC 是目前最稳的演示链路；默认 `cs_eval_questions.jsonl` 与 Power PMAC 索引不匹配，会合理返回 `No supporting reference found.`。
- 正式目标模型 `Qwen3-VL-8B` 仍未部署；当前实际使用的是 `qwen-8b-instruct-baseline`。
- OCR fallback 尚未实现，只能记录 OCR todo。
- 三学科正式评测集、ground truth 和最终指标报告尚未完成。
- Chroma telemetry 警告不影响结果：`Failed to send telemetry event ...`。
- Windows 终端如显示中文乱码，需设置 UTF-8 输出。

---

## Power PMAC 自问自答使用方式

### 推荐方式：直接单问

现在已经支持直接提问：

```powershell
cd D:\program\code\Python\kd-agent-pipeline

powershell -ExecutionPolicy Bypass -File scripts\ask_power_pmac.ps1 "What phone number is listed for Delta Tau Data Systems technical support?"
```

也可以不带问题运行，脚本会提示输入：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\ask_power_pmac.ps1
```

输出会显示：

- `Question`
- `Result`
- `Retrieved references`
- `Mode`
- `Latency`
- `Tokens`

每次单问结果会追加到：

```text
outputs/system/manual_power_pmac_results.jsonl
```

### 批量方式：JSONL 问题文件

如果想一次问多条问题，可以继续使用 JSONL 批量问答。

### 1. 新建自己的问题文件

例如创建：

```text
D:\program\code\Python\kd-agent-pipeline\data\eval\my_power_pmac_questions.jsonl
```

每一行是一个 JSON，格式如下：

```json
{"id":"my_001","discipline":"power_pmac","question":"What is the purpose of the Power PMAC Script language?"}
{"id":"my_002","discipline":"power_pmac","question":"How does Power PMAC describe a PLC program?"}
{"id":"my_003","discipline":"power_pmac","question":"According to the manual, what should qualified personnel do before installing equipment?"}
```

注意：

- 每个问题必须单独一行。
- `id` 不要重复。
- 英文问题会更稳定；中文问题也能跑，但如果手册原文主要是英文，英文提问更容易检索到证据。

### 2. 用 Power PMAC 索引运行问答

在 PowerShell 里运行：

```powershell
cd D:\program\code\Python\kd-agent-pipeline

conda activate kd-agent-pipeline-gpu

$env:KD_AGENT_PROJECT_ROOT="D:\program\code\Python\kd-agent-pipeline"
$env:NO_PROXY="localhost,127.0.0.1,::1"
$env:no_proxy="localhost,127.0.0.1,::1"
$env:PYTHONIOENCODING="utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$env:KD_AGENT_SYSTEM_EVAL_PATH="D:\program\code\Python\kd-agent-pipeline\data\eval\my_power_pmac_questions.jsonl"
$env:KD_AGENT_SYSTEM_OUTPUT_PATH="D:\program\code\Python\kd-agent-pipeline\outputs\system\my_power_pmac_results.jsonl"
$env:KD_AGENT_SYSTEM_REPORT_PATH="D:\program\code\Python\kd-agent-pipeline\reports\my_power_pmac_report.md"

python src\agent\run_system_rag.py
python scripts\05_generate_system_report.py
```

如果你不想依赖 `conda activate`，用更稳的方式：

```powershell
$env:PATH="D:\program\tool\anaconda\envs\kd-agent-pipeline-gpu\Library\bin;D:\program\tool\anaconda\envs\kd-agent-pipeline-gpu\Scripts;D:\program\tool\anaconda\envs\kd-agent-pipeline-gpu;$env:PATH"

& "D:\program\tool\anaconda\envs\kd-agent-pipeline-gpu\python.exe" src\agent\run_system_rag.py
& "D:\program\tool\anaconda\envs\kd-agent-pipeline-gpu\python.exe" scripts\05_generate_system_report.py
```

### 3. 查看答案

主要看这两个文件：

```text
outputs/system/my_power_pmac_results.jsonl
reports/my_power_pmac_report.md
```

其中：

- `answer` 是模型回答。
- `retrieved` 是检索到的证据 chunk。
- `response_mode` 应该是 `ollama`。
- 如果回答是 `No supporting reference found.`，表示当前检索片段没有足够证据支撑答案。

---

## 阶段 0：锁定本地可运行状态

**涉及文件：**

- `AGENTS.md`
- `src/common/paths.py`
- `src/common/system_pipeline_paths.py`
- `src/common/console_text.py`
- `tests/test_system_pipeline_paths.py`
- `tests/test_console_text.py`

- [x] **确认当前分支**

```powershell
git branch --show-current
```

预期：

```text
local/windows-deploy
```

- [x] **确认 Python/CUDA/cuDNN 可用**

推荐方式：

```powershell
conda activate kd-agent-pipeline-gpu
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.backends.cudnn.version())"
```

预期：

```text
2.12.1
True
92301
```

- [x] **确认 Ollama 可用**

```powershell
ollama --version
ollama list
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:11434/api/tags
```

预期模型：

```text
qwen-8b-instruct-baseline:latest
qwen3:8b
```

---

## 阶段 1：Power PMAC system 演示闭环

**涉及文件：**

- `data/raw/Power PMAC Software Reference Manual.pdf`
- `data/eval/power_pmac_smoke_questions.jsonl`
- `src/parser/parse_pdf_pages.py`
- `src/chunker/build_text_chunks.py`
- `src/indexer/build_system_index.py`
- `src/agent/run_system_rag.py`
- `src/agent/answer_postprocess.py`
- `scripts/05_generate_system_report.py`
- `outputs/system/power_pmac_results.jsonl`
- `reports/power_pmac_system_report.md`

- [x] **接入 Power PMAC 原始 PDF**

原始文件路径：

```text
D:\program\code\Python\kd-agent-pipeline\data\raw\Power PMAC Software Reference Manual.pdf
```

- [x] **生成 system 索引**

```powershell
python src\parser\parse_pdf_pages.py
python src\chunker\build_text_chunks.py
python src\indexer\build_system_index.py
```

已生成：

```text
data/processed/
data/indexes/chroma_system/
```

- [x] **运行 Power PMAC smoke 问答**

```powershell
$env:KD_AGENT_SYSTEM_EVAL_PATH="D:\program\code\Python\kd-agent-pipeline\data\eval\power_pmac_smoke_questions.jsonl"
$env:KD_AGENT_SYSTEM_OUTPUT_PATH="D:\program\code\Python\kd-agent-pipeline\outputs\system\power_pmac_results.jsonl"
$env:KD_AGENT_SYSTEM_REPORT_PATH="D:\program\code\Python\kd-agent-pipeline\reports\power_pmac_system_report.md"

python src\agent\run_system_rag.py
python scripts\05_generate_system_report.py
```

当前验收状态：

- `response_mode=ollama`
- 无 `/think` 泄漏
- 有证据的问题能回答
- 无证据的问题返回 `No supporting reference found.`

- [x] **增加 Power PMAC 单问脚本**

已新增：

```text
scripts/ask_power_pmac.ps1
src/agent/ask_system_once.py
```

目标用法：

```powershell
.\scripts\ask_power_pmac.ps1 "What is a PLC program in Power PMAC?"
```

当前验收状态：

- 能直接输入一个问题并返回答案。
- 会显示检索到的引用页。
- 会把结果追加到 `outputs/system/manual_power_pmac_results.jsonl`。
- 验证问题可返回 `response_mode=ollama`。

---

## 阶段 2：报告指标补强

**涉及文件：**

- `scripts/05_generate_system_report.py`
- `reports/power_pmac_system_report.md`
- `reports/local_windows_test_summary.md`

- [x] **生成类似截图的 system 报告**

当前报告已包含：

- 原始 chunk 数
- 高质量 chunk 数
- OCR todo 页
- 测试问题数
- 平均延迟
- 平均 Token
- 回答/未找到统计

- [ ] **补充更适合答辩的指标**

需要继续补：

- 平均输入 Token
- 平均输出 Token
- `response_mode=ollama` 占比
- `No supporting reference found` 占比
- 引用命中页统计
- 检索 top-k 命中摘要

- [ ] **生成一份 Power PMAC 专项验收报告**

建议文件：

```text
reports/power_pmac_acceptance_report.md
```

内容包括：

- 环境版本
- PDF 页数与 chunk 数
- 模型名称
- Ollama 服务状态
- 5 个 smoke 问题结果
- 已知限制
- 下一步计划

---

## 阶段 3：正式评测集

**涉及文件：**

- `data/eval/formal_questions.jsonl`
- `data/eval/formal_ground_truth.jsonl`
- `docs/datasets.md`

- [ ] **确定正式三学科数据**

目录建议：

```text
data/raw/cs/
data/raw/medical/
data/raw/law/
```

最低目标：

- 每个学科至少 1 份 100 页以上文档。
- 每个学科至少 20 个问题。
- 每个问题有期望关键词和证据页。

- [ ] **建立 ground truth**

示例：

```json
{"id":"power_pmac_001","discipline":"power_pmac","question":"What phone number is listed for Delta Tau Data Systems technical support?","expected_keywords":["818","717","5656"],"evidence":[{"source_file":"Power PMAC Software Reference Manual.pdf","page":1}],"answer_language":"en"}
```

- [ ] **记录数据集来源**

建议文件：

```text
docs/datasets.md
```

---

## 阶段 4：OCR fallback

**涉及文件：**

- `src/parser/ocr_pdf_pages.py`
- `src/parser/parse_pdf_pages.py`
- `src/chunker/build_text_chunks.py`
- `tests/test_ocr_records.py`

- [ ] **定义 OCR 输出契约**

目标记录：

```json
{"source_file":"example.pdf","page":12,"parse_method":"ocr","text":"...","needs_ocr":false,"ocr_status":"completed","citation_anchor":"example.pdf#page=12"}
```

- [ ] **优先接入一个本地 OCR 后端**

推荐顺序：

```text
PaddleOCR -> Tesseract -> marker/unstructured fallback
```

- [ ] **增加 OCR smoke test**

```powershell
python -m unittest tests.test_ocr_records -v
```

---

## 阶段 5：正式评测指标

**涉及文件：**

- `src/eval/evaluate_results.py`
- `scripts/07_evaluate_formal.py`
- `reports/formal_evaluation.md`

- [ ] **实现正式指标计算**

至少输出：

- Hit@5
- 引用正确率
- 答案关键词覆盖率
- 无引用生成率
- 平均输入/输出/总 Token
- 平均延迟
- 文档处理吞吐

- [ ] **加入 FY27 验收目标**

报告中明确写出：

```text
Token efficiency target: system total tokens <= 60% of baseline.
Recall target: Hit@5 >= 85%.
Hallucination target: no-citation generation <= 15%.
Throughput target: >= 15 pages/minute for document processing.
```

---

## 阶段 6：检索质量与 Token 成本优化

**涉及文件：**

- `src/agent/run_system_rag.py`
- `src/indexer/build_system_index.py`
- `src/retrieval/context_filter.py`
- `src/retrieval/rerank.py`

- [ ] **增加低质量 chunk 过滤**

过滤或降权：

```text
is_low_quality == true
content_role in ["table_or_layout_fragment", "noisy_layout", "weak_semantic_text"]
quality_score < 0.60
```

- [ ] **增加动态 top-k**

建议：

```text
高置信检索：top_k=3
低置信检索：top_k=6
```

- [ ] **增加上下文压缩**

目标：只把与问题直接相关的证据句送入模型，减少输入 Token。

- [ ] **生成消融报告**

建议文件：

```text
reports/ablation_retrieval_token_cost.md
```

---

## 阶段 7：Qwen3-VL-8B 与 LoRA

**涉及文件：**

- `configs/Modelfile.system`
- `scripts/build_system_ollama_model.sh`
- `configs/lora_config.yaml`
- `src/finetune/prepare_lora_data.py`
- `src/finetune/train_lora.py`

- [ ] **确认 Qwen3-VL-8B 模型产物**

当前尚未完成：

```text
models/gguf/Qwen3-VL-8B.gguf
qwen3-vl-8b-system
```

- [ ] **构建正式 system Ollama 模型**

```powershell
$env:KD_AGENT_SYSTEM_GGUF="D:\program\code\Python\kd-agent-pipeline\models\gguf\Qwen3-VL-8B.gguf"
bash scripts/build_system_ollama_model.sh
ollama list
```

- [ ] **LoRA 保持为可选项**

只有当 RAG、prompt、检索优化无法达到验收指标时，再推进 LoRA。

---

## 阶段 8：最终交付物

**涉及文件：**

- `docs/architecture.md`
- `docs/data_flow.md`
- `docs/deployment.md`
- `docs/known_limits.md`
- `reports/final_evaluation.md`

- [ ] **补齐架构文档**

章节建议：

```markdown
# Architecture

## Input Layer
## Parsing Layer
## Chunking Layer
## Indexing Layer
## Retrieval And Agent Layer
## Ollama Deployment Layer
## Evaluation Layer
```

- [ ] **补齐部署文档**

必须写清：

- Conda 环境
- Ollama 安装和启动
- `NO_PROXY/no_proxy`
- CUDA/cuDNN 路径问题
- Power PMAC 自问自答方式

- [ ] **补齐最终评测报告**

最终报告至少包含：

- baseline 与 system 指标对比
- Token 成本
- 平均延迟
- 吞吐
- 引用正确率
- OCR 覆盖说明
- 已知限制

---

## 近期推荐执行顺序

1. 完善 `reports/power_pmac_acceptance_report.md`，把 Power PMAC 演示闭环固化。
2. 补正式评测脚本 `scripts/07_evaluate_formal.py`。
3. 再做 OCR fallback。
4. 扩展三学科数据集。
5. 最后补齐正式交付文档。
