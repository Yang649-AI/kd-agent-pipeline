# Raw PDF 计算机教材评测记录

## 数据源

- 原始目录：`/root/autodl-tmp/kd_agent_pipeline/data/raw/cs`
- `cs-cn.pdf`：441 页，PyMuPDF 可抽取文字页数 0，需要 OCR。
- `cs-eg.pdf`：1120 页，PyMuPDF 可抽取文字页数 1114，已进入索引。

## 索引与指标

- 加载文档页：1114
- 文档页来源：{'cs-eg.pdf': 1114}
- chunk 数：1902
- 测试问题数：6
- 答案关键词命中率：0.00%
- 无引用生成/幻觉率：0.00%
- 平均延迟：0.0061 s
- 平均总 Token：308.33
- 平均上下文压缩比例：17.73%

## 样例结果

### cs_001

问题：What is virtual memory and why is it useful?

回答：.. [S1] j , [S1] ' [S1]

检索来源：
- rank=1, score=0.15637, source=cs-eg.pdf, chunk=cs-eg:p837:c001
- rank=2, score=0.156213, source=cs-eg.pdf, chunk=cs-eg:p690:c001
- rank=3, score=0.153432, source=cs-eg.pdf, chunk=cs-eg:p863:c002

### cs_002

问题：What state and resources are associated with a process?

回答：Section 12.3 Concurrent Programming with Threads [S3] 989 [S3] •;.The threat! [S3]

检索来源：
- rank=1, score=0.132335, source=cs-eg.pdf, chunk=cs-eg:p769:c001
- rank=2, score=0.132178, source=cs-eg.pdf, chunk=cs-eg:p953:c002
- rank=3, score=0.126845, source=cs-eg.pdf, chunk=cs-eg:p1024:c001

### cs_003

问题：How does cache memory exploit locality?

回答：630 [S4] Chapter 6 The Memory Hierarchy [S4] B. [S4]

检索来源：
- rank=1, score=0.218187, source=cs-eg.pdf, chunk=cs-eg:p640:c002
- rank=2, score=0.212731, source=cs-eg.pdf, chunk=cs-eg:p49:c002
- rank=3, score=0.210114, source=cs-eg.pdf, chunk=cs-eg:p48:c002

### cs_004

问题：Give examples of exceptional control flow in operating systems.

回答：We then move up a level of abstraction and describe processes [S1] an,d signals, which lie <;t the intersection of applications and the op~rating system. [S1] Finally, we discuss nonlocal jumps, which are an application-level form of ECF. [S1]

检索来源：
- rank=1, score=0.203223, source=cs-eg.pdf, chunk=cs-eg:p758:c002
- rank=2, score=0.172132, source=cs-eg.pdf, chunk=cs-eg:p791:c001
- rank=3, score=0.15861, source=cs-eg.pdf, chunk=cs-eg:p822:c001

### cs_005

问题：What does Amdahl's Law say about system speedup?

回答：Section 1.9 Important Themes [S1] 23 [S1] A. [S1]

检索来源：
- rank=1, score=0.2172, source=cs-eg.pdf, chunk=cs-eg:p58:c001
- rank=2, score=0.208264, source=cs-eg.pdf, chunk=cs-eg:p57:c001
- rank=3, score=0.178153, source=cs-eg.pdf, chunk=cs-eg:p603:c002

### cs_006

问题：How does RAG reduce hallucination in an educational agent?

回答：Section 5.8 Loop Unrolling [S2] 531 [S2] 4 [S2]

检索来源：
- rank=1, score=0.10751, source=cs-eg.pdf, chunk=cs-eg:p319:c002
- rank=2, score=0.088911, source=cs-eg.pdf, chunk=cs-eg:p566:c001
- rank=3, score=0.087874, source=cs-eg.pdf, chunk=cs-eg:p484:c002

## 结论

当前 raw PDF 测试证明英文教材可直接进入本地蒸馏与检索评测；中文教材是扫描版，必须补 OCR 后才能参与中文内容评测。