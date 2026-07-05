# Baseline 与 System 管线对比报告

## 1. 报告目的

本报告用于对比 baseline 管线与当前正式 system 管线在同一组 smoke test 问题上的运行结果。对比内容包括问答覆盖情况、检索片段数量、回答状态以及系统管线相对于 baseline 的结构化改进。

## 2. 对比对象

| 对比项 | Baseline 管线 | 当前 System 验证管线 |
|---|---|---|
| 角色 | baseline 复现 | 正式系统管线 smoke test 验证 |
| 配置文件 | `configs/baseline_config.yaml` | `configs/system_config.yaml` |
| 文档解析 | LangChain 默认 PDF 加载 | `src/parser/parse_pdf_pages.py` 分页解析 |
| 文本分块 | 标准文本切分 | 带质量标注的结构化分块 |
| 向量库 | Chroma | Chroma |
| 问答模型 | Qwen 8B 级 Ollama 验证模型 | 临时 Ollama 验证模型 |
| 正式目标模型 | 不适用 | Qwen3-VL-8B |
| OCR / 多模态处理 | 未覆盖 | 已记录 OCR todo，后续接入多模态解析 |

## 3. 总体指标对比

| 指标 | Baseline | System 验证管线 |
|---|---:|---:|
| 问题总数 | 4 | 4 |
| 成功回答数 | 4 | 4 |
| 未找到参考资料数 | 0 | 0 |
| 回答覆盖率 | 100.00% | 100.00% |
| 平均检索片段数 | 5.00 | 4.00 |
| 平均 token 数 | 1321.25 | 1216.00 |

## 4. 单问题结果对比

| ID | 问题 | Baseline 状态 | System 状态 | Baseline 回答预览 | System 回答预览 |
|---|---|---|---|---|---|
| cs_eg_001 | What is virtual memory in computer systems? | 已回答 | 已回答 | Virtual memory is an abstraction that provides each process with the illusion that it has exclusive use of the main memory. It creates a large, uniform, and private address space f... | Answer: Virtual memory is an abstraction of main memory that allows processors to reference main memory using virtual addressing. It translates virtual addresses into physical addr... |
| cs_eg_002 | What is a process in an operating system? | 已回答 | 已回答 | A process in an operating system is the system's abstraction for a running program. It provides the illusion that a program has exclusive use of the processor and memory, even thou... | Answer: A process is the operating system’s abstraction for a running program. It provides the illusion that a program has exclusive use of the processor, main memory, and I/O devi... |
| cs_eg_003 | What is cache memory? | 已回答 | 已回答 | Cache memory is a type of high-speed memory used to store frequently accessed data, allowing for faster access compared to main memory (like DRAM). It helps reduce the time it take... | Answer: Cache memory is a type of high-speed memory used to store frequently accessed data, allowing faster access compared to main memory. It works by storing copies of data from ... |
| cs_eg_004 | What is exceptional control flow? | 已回答 | 已回答 | Exceptional control flow refers to changes in the control flow that occur outside the normal branches and procedure calls. It includes examples such as hardware exceptions and inte... | Answer: Exceptional control flow (ECF) refers to the mechanism that handles unexpected or exceptional conditions during program execution. It allows programs to react to changes in... |

## 5. System 管线相对于 Baseline 的改进点

当前 system 管线并不是简单复刻 baseline，而是在 baseline 基础上增加了以下工程化能力：

1. **分页级 PDF 解析**：将 PDF 按页解析并保留页码、来源文件、学科类别和引用锚点。
2. **结构化知识块生成**：在分块阶段保留 chunk_id、source_file、page、citation_anchor 等元数据。
3. **知识块质量标注**：为每个 chunk 增加 `quality_score`、`is_low_quality`、`quality_reasons` 和 `content_role` 字段。
4. **OCR 待处理页记录**：对扫描页或图片页生成 `ocr_todo_pages.jsonl`，为后续 OCR 或多模态解析预留入口。
5. **正式系统配置分离**：通过 `configs/system_config.yaml` 明确正式系统目标模型为 `Qwen3-VL-8B`。
6. **Ollama 兼容部署模板**：通过 `configs/Modelfile.system` 和 `scripts/build_system_ollama_model.sh` 预留正式系统模型构建流程。

## 6. 当前阶段说明

当前 system RAG runner 仍属于管线验证阶段，使用临时 Ollama 文本模型验证解析、分块、索引、检索、问答与引用输出流程。正式系统目标模型已在 `configs/system_config.yaml` 中明确为 `Qwen3-VL-8B`，后续需要继续接入 OCR、多模态页面解析和 LoRA 微调流程。

本报告属于 smoke test 对比报告，不等同于最终性能评测报告。后续应扩展更大规模测试集，并加入引用正确性、答案忠实性、幻觉率、响应延迟和多模态文档覆盖率等指标。
