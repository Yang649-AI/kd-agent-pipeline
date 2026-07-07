# 高效自动化知识蒸馏与智能体生成管线评估报告

生成时间：2026-07-06 21:15:20

## 1. 评测范围

本轮按用户要求仅使用计算机学科数据集进行闭环验证，暂不做医学、法学三学科扩展。
数据集位于 `data/sample/cs/` 与 `data/eval/cs_eval_questions.jsonl`，包含操作系统、体系结构、异常控制流、Amdahl 定律、RAG 等主题的 ground truth 标注。

## 2. 系统方案

- 多格式解析：支持 Markdown/TXT/JSONL/PDF/EPUB，并为图片、音频保留本地 OCR/ASR 降级占位链路。
- 自适应分块：优先保留标题层级与语义句边界，记录学科、来源、模态、关键词和页码元数据。
- 结构化蒸馏：将原始资料封装为轻量 chunk JSON 索引，不做权重蒸馏。
- 检索增强：使用本地 TF-IDF/关键词评分，避免在无网络或无 GPU 环境下阻塞。
- 上下文压缩：按问题筛选证据句，控制进入生成端的 token 预算。
- Citation Grounding：答案必须带 `[Sx]` 引用锚点，无依据时输出 `未找到参考资料`。

## 3. 索引统计

- chunk 数：7
- 平均 chunk token：59.29
- 最大 chunk token：84

## 4. 指标结果

- 测试问题数：6
- Hit@5：100.00%
- 答案关键词命中率：100.00%
- 无引用生成/幻觉率：0.00%
- 平均延迟：0.0006 s
- 平均输入 Token：304.83
- 平均输出 Token：63.67
- 平均总 Token：368.50
- 平均上下文压缩比例：68.52%
- 平均总 Token 比例：baseline 尚未在当前环境生成，报告先记录系统实测值。

## 5. 消融说明

| 设置 | 预期影响 | 当前实现记录 |
| --- | --- | --- |
| 关闭上下文压缩 | Token 上升，可能提高少量召回 | 当前报告记录压缩比例，可用 `compressed_context_tokens` 调大模拟 |
| 固定长度分块 | 标题/证据边界破碎 | baseline 使用固定 chunk_size=1000 作为对照 |
| 关闭引用约束 | 幻觉率上升 | 当前 agent 默认拒绝无依据回答 |
| Q4/Q5 量化切换 | 显存、延迟、质量权衡 | Ollama Modelfile 已提供 Q4 路径，后续替换 GGUF 即可复测 |

## 6. 样例结果

### cs_001

问题：What is virtual memory and why is it useful?

回答：Virtual memory is an abstraction that gives each process the illusion of a large, private, contiguous address space. [S1] The operating system and hardware memory management unit translate virtual addresses to physical addresses through page tables. [S1] Virtual memory supports protection between processes, controlled sharing, demand paging, and efficient use of physical memory. [S1]

Hit@5：True，引用：S1

### cs_002

问题：What state and resources are associated with a process?

回答：A process is an instance of a running program together with its private virtual address space, open files, register state, and other operating-system resources. [S1] The operating system schedules processes on CPUs and switches between them by saving the current context and restoring another context. [S1] Context switching lets multiple programs share processors, but it has overhead because registers, page-table state, and cache locality may change. [S1]

Hit@5：True，引用：S1

### cs_003

问题：How does cache memory exploit locality?

回答：Cache memory is a small and fast storage layer placed close to the processor. [S1] It exploits temporal locality, where recently used data is likely to be used again, and spatial locality, where nearby data is likely to be used soon. [S1] Caches are usually organized into sets and lines; a miss occurs when requested data is not present and must be fetched from a lower level of the memory hierarchy. [S1]

Hit@5：True，引用：S1

### cs_004

问题：Give examples of exceptional control flow in operating systems.

回答：Exceptional control flow is any abrupt change in the normal sequence of instruction execution. [S1] Hardware exceptions, interrupts, traps, faults, process context switches, and Unix signals are examples. [S1] Exceptional control flow allows operating systems to respond to I/O events, system calls, arithmetic errors, page faults, and interprocess communication while preserving a controlled execution model. [S1]

Hit@5：True，引用：S1

### cs_005

问题：What does Amdahl's Law say about system speedup?

回答：Amdahl's Law estimates the maximum speedup from optimizing part of a system. [S1] If fraction p of execution time can be improved by a factor s, total speedup is 1 / ((1 - p) + p / s). [S1] The law shows that the non-optimized portion eventually dominates performance, so optimization effort should focus on the common case and on bottlenecks with large execution share. [S1]

Hit@5：True，引用：S1

### cs_006

问题：How does RAG reduce hallucination in an educational agent?

回答：Retrieval-augmented generation, or RAG, answers a question by retrieving relevant evidence from an external knowledge base and then conditioning generation on that evidence. [S1] In a grounded educational agent, RAG reduces hallucination by requiring answers to cite retrieved passages. [S1] The main retrieval quality metric used in this project is Hit@5, which is true when at least one of the top five retrieved chunks matches the annotated evidence. [S1]

Hit@5：True，引用：S1

## 7. 已知边界与后续迭代

- 当前补齐的是计算机单学科小型可复现数据集，不代表最终 ≥100 页正式教材评测规模。
- 图片与音频路径已纳入解析框架，但正式 OCR/ASR 需在有依赖时接入 PaddleOCR、Tesseract、whisper.cpp 或 faster-whisper。
- 若接入 Ollama 生成模型，建议保持本地检索和引用守卫不变，只替换 `grounded_extractive_answer` 的生成阶段。
- 三学科扩展时只需新增 `data/sample/{medicine,law}` 与对应 eval JSONL，再按同一脚本运行。
