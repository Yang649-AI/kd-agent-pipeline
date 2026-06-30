# Baseline 复现实验记录

生成时间：2026-06-29 20:20:34

## 1. Baseline 名称

LangChain + 标准 RAG + Qwen-8B-Instruct

## 2. 实际运行模型

- 运行框架：Ollama
- 实际模型名称：qwen-8b-instruct-baseline
- 模型来源：Qwen3-8B-Q4_K_M.gguf 通过 Ollama Modelfile 构建
- 模型用途：用于复现 Qwen-8B-Instruct 对比基线

## 3. RAG 配置

- 向量库：Chroma
- Embedding 模型：BAAI/bge-small-zh-v1.5
- 分块方式：RecursiveCharacterTextSplitter 固定长度切分
- chunk_size：1000
- chunk_overlap：200
- top_k：5
- temperature：0
- num_ctx：4096

## 4. 未启用的优化项

- 未启用自适应分块
- 未启用重排序 rerank
- 未启用上下文压缩
- 未启用动态 Top-K
- 未启用 LoRA 微调

## 5. 当前 smoke test 指标

- 测试问题数：4
- 平均延迟：2.68 s
- 最大延迟：4.50 s
- 最小延迟：1.17 s
- 平均输入 Token：1213.50
- 平均输出 Token：107.75
- 平均总 Token：1321.25
- 总 Token：5285

## 6. Smoke test 问答样例

### cs_eg_001

问题：What is virtual memory in computer systems?

回答摘要：Virtual memory is an abstraction that provides each process with the illusion that it has exclusive use of the main memory. It creates a large, uniform, and private address space for each process, allowing efficient use of main memory by treating it as a cache for data stored on disk. Virtual memory simplifies memory management by providing a consistent view of memory to each process and protects processes from corrupting each other's address spaces. It works silently and automatically without r

检索来源：
- [1] cs-eg.pdf，page=836
- [2] cs-eg.pdf，page=52
- [3] cs-eg.pdf，page=836
- [4] cs-eg.pdf，page=205
- [5] cs-eg.pdf，page=862

### cs_eg_002

问题：What is a process in an operating system?

回答摘要：A process in an operating system is the system's abstraction for a running program. It provides the illusion that a program has exclusive use of the processor and memory, even though multiple processes may run concurrently on the same system. Key abstractions include:   1. **Logical control flow**: Creates the appearance of sequential execution for a single program, despite interleaving with other processes.   2. **Private address space**: Isolates the program's code and data, making it seem as 

检索来源：
- [1] cs-eg.pdf，page=768
- [2] cs-eg.pdf，page=50
- [3] cs-eg.pdf，page=49
- [4] cs-eg.pdf，page=766
- [5] cs-eg.pdf，page=766

### cs_eg_003

问题：What is cache memory?

回答摘要：Cache memory is a type of high-speed memory used to store frequently accessed data, allowing for faster access compared to main memory (like DRAM). It helps reduce the time it takes for the CPU to access data by keeping copies of frequently used data in a smaller, faster storage location. In the context of virtual memory systems, cache memories like SRAM caches (L1, L2, L3) are used between the CPU and main memory, while DRAM caches refer to the virtual memory system's caching of virtual pages i

检索来源：
- [1] cs-eg.pdf，page=843
- [2] cs-eg.pdf，page=656
- [3] cs-eg.pdf，page=587
- [4] cs-eg.pdf，page=840
- [5] cs-eg.pdf，page=662

### cs_eg_004

问题：What is exceptional control flow?

回答摘要：Exceptional control flow refers to changes in the control flow that occur outside the normal branches and procedure calls. It includes examples such as hardware exceptions and interrupts, context switches between concurrent processes, abrupt changes caused by Linux signals, and nonlocal jumps in C that break the stack discipline.

检索来源：
- [1] cs-eg.pdf，page=22
- [2] cs-eg.pdf，page=768
- [3] cs-eg.pdf，page=756
- [4] cs-eg.pdf，page=798
- [5] cs-eg.pdf，page=767

## 7. 当前数据集说明

- `cs-eg.pdf` 可以被 PyMuPDF 正常抽取文字，并已成功构建 baseline 向量库。
- `cs-cn.pdf` 为扫描版或图片版 PDF，PyMuPDF 抽取前 10 页文字长度均为 0，因此未进入当前 baseline 向量库。
- 当前结果用于验证 baseline 工程链路，不作为最终三学科正式评测结果。

## 8. 后续工作

- 准备可抽取文字的中文资料，或在正式系统中加入 OCR 解析流程。
- 构建正式评测集，补充标准答案、证据页码和 Hit@5 评价。
- 与后续优化系统进行 Token 消耗、延迟、Hit@5 和无引用生成比例对比。
