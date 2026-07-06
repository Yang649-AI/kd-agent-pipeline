# 双语计算机教材评测报告

## 数据源

- 中文教材：`cs-cn.pdf`，扫描版，使用 Tesseract `chi_sim+eng` 对代表页 OCR 后入索引。
- 英文教材：`cs-eg.pdf`，使用原系统清洗后的高质量文本 chunk 入索引。
- 评测要求：中文问题必须中文回答，英文问题必须英文回答；检索索引同时包含两本教材，并通过术语扩展支持跨语言检索。

## 指标

- 中文 OCR chunk 数：54
- 英文文本 chunk 数：1572
- 总 chunk 数：1626
- 测试问题数：8
- 回答语言匹配率：100.00%
- 平均答案关键词召回：70.83%
- 无引用生成/幻觉率：0.00%
- 平均延迟：0.0056 s
- 平均总 Token：543.25
- 平均上下文压缩比例：40.56%

## 样例结果

### zh_ml_001

问题：什么是假设空间？

回答：我们可以把学习过程看作一个在所有假设(hypothesis)组成的空间中进行 _ [S1] 需注意的是, 现实问题中我们常面临很大的假设空间, 但学习过程是基于 [S2] 训练集一致的“假设集合”, 我们称之为“版本空间”(version space). [S2]

期望语言：zh；实际语言：zh；语言匹配：True
关键词召回：66.67%

检索来源：
- rank=1, score=0.300776, source=cs-cn.pdf, citation=cs-cn.pdf:p21#cs-cn:p21:c001
- rank=2, score=0.262472, source=cs-cn.pdf, citation=cs-cn.pdf:p21#cs-cn:p21:c003
- rank=3, score=0.198721, source=cs-cn.pdf, citation=cs-cn.pdf:p22#cs-cn:p22:c001

### zh_ml_002

问题：查准率和查全率分别关注什么？

回答：户感兴趣的信息中有多少被检索出来了”，“查准率”(precision)与“查全 [S2] 通常只有在一些简单任务中, 才可能使查全率和查准率都很高. [S3] 是比较 P-R 曲线下面积的大小, 它在一定程度上表征了学习器在查准率和查全 [S4]

期望语言：zh；实际语言：zh；语言匹配：True
关键词召回：66.67%

检索来源：
- rank=1, score=0.316443, source=cs-cn.pdf, citation=cs-cn.pdf:p46#cs-cn:p46:c002
- rank=2, score=0.260437, source=cs-cn.pdf, citation=cs-cn.pdf:p46#cs-cn:p46:c001
- rank=3, score=0.249905, source=cs-cn.pdf, citation=cs-cn.pdf:p47#cs-cn:p47:c001

### zh_ml_003

问题：线性回归试图学习什么样的函数？

回答：这就是“对数线性回归”(log-linear regression), 它实际上是在试图让 ewr=ttb [S1] 空间的非线性函数映射, 如图 3.1 所示. [S1] on 归纳偏好的作用在图 1.3 这个回归学习图示中可能更直观. [S2]

期望语言：zh；实际语言：zh；语言匹配：True
关键词召回：66.67%

检索来源：
- rank=1, score=0.29839, source=cs-cn.pdf, citation=cs-cn.pdf:p72#cs-cn:p72:c002
- rank=2, score=0.230867, source=cs-cn.pdf, citation=cs-cn.pdf:p22#cs-cn:p22:c003
- rank=3, score=0.229865, source=cs-cn.pdf, citation=cs-cn.pdf:p71#cs-cn:p71:c001

### zh_cross_001

问题：虚拟内存提供了哪些能力？

回答：根据英文教材证据，虚拟内存是对主存的抽象，为每个进程提供统一而私有的地址空间；它把磁盘上的地址空间按页缓存在主存中，提高主存利用率，并通过页表和保护位支持内存管理、共享与保护。 [S1]

期望语言：zh；实际语言：zh；语言匹配：True
关键词召回：100.00%

检索来源：
- rank=1, score=0.318858, source=cs-eg.pdf, citation=cs-eg.pdf:p909#cs_cs-eg_pdf_p909_c2
- rank=2, score=0.264616, source=cs-eg.pdf, citation=cs-eg.pdf:p909#cs_cs-eg_pdf_p909_c3
- rank=3, score=0.263756, source=cs-eg.pdf, citation=cs-eg.pdf:p853#cs_cs-eg_pdf_p853_c3

### en_cs_001

问题：What capabilities does virtual memory provide?

回答：In order to manage memory more efficiently and with fewer errors, modern systems provide an abstraction of main memory known as virtual memory (VM). [S1] With one clean mech- anism, virtual memory provides three important capabilities: (1) It uses main memory efficiently by treating it as a cache for an address space stored on disk, keeping only the active areas in main memory and transferring data back and forth between disk and memory as needed. [S1] Understanding virtual memory will help you harness its powerful capabilities in your applications. [S3]

期望语言：en；实际语言：en；语言匹配：True
关键词召回：66.67%

检索来源：
- rank=1, score=0.088832, source=cs-eg.pdf, citation=cs-eg.pdf:p836#cs_cs-eg_pdf_p836_c1
- rank=2, score=0.084477, source=cs-cn.pdf, citation=cs-cn.pdf:p95#cs-cn:p95:c002
- rank=3, score=0.080924, source=cs-eg.pdf, citation=cs-eg.pdf:p836#cs_cs-eg_pdf_p836_c3

### en_cs_002

问题：What is Amdahl's law and how does it limit total speedup?

回答：, One interesting SP\'!'ial case of Amdahl's law is to c9nsider the effect of setting k to oo. [S1] The main idea is that when we speed up one part of a system, the effect on the overall sys- tem performance depends on both how significant this part was and how much it sped up. [S4] That is, we are able to take some part of the system and speed it up to the point.at which it takes I\ negligibl<; ~ount of time. [S1]

期望语言：en；实际语言：en；语言匹配：True
关键词召回：33.33%

检索来源：
- rank=1, score=0.13763, source=cs-eg.pdf, citation=cs-eg.pdf:p57#cs_cs-eg_pdf_p57_c1
- rank=2, score=0.113863, source=cs-eg.pdf, citation=cs-eg.pdf:p602#cs_cs-eg_pdf_p602_c2
- rank=3, score=0.106947, source=cs-cn.pdf, citation=cs-cn.pdf:p47#cs-cn:p47:c003

### en_cs_003

问题：What is exceptional control flow in a computer system?

回答：8.8 Summary Exceptional control flow (ECF) occurs at all levels of a computer system and is a basic mechanism for providing concurrency in a computer system .. [S4] We cover examples of exceptional control flow that exist at all levels of the system, from low-level hardware ex- ceptions and interrupts, to context switches between concurrent processes, to abrupt changes in control flow caused by the receipt of Linux signals, to the nonlocal jumps in C that break the stack discipline. [S1] 8.2.S Context Switches The operating system kernel implements multitasking using a higher-level fonn of exceptional control flow known as a context switch. [S3]

期望语言：en；实际语言：en；语言匹配：True
关键词召回：66.67%

检索来源：
- rank=1, score=0.157546, source=cs-eg.pdf, citation=cs-eg.pdf:p22#cs_cs-eg_pdf_p22_c2
- rank=2, score=0.145785, source=cs-cn.pdf, citation=cs-cn.pdf:p30#cs-cn:p30:c003
- rank=3, score=0.13016, source=cs-eg.pdf, citation=cs-eg.pdf:p770#cs_cs-eg_pdf_p770_c0

### en_cross_001

问题：What is a hypothesis space in machine learning?

回答：Based on the Chinese textbook evidence, a hypothesis space is the set of all candidate hypotheses considered by a learning algorithm. Learning can be viewed as searching this space for hypotheses that fit the training examples. [S1]

期望语言：en；实际语言：en；语言匹配：True
关键词召回：100.00%

检索来源：
- rank=1, score=0.39691, source=cs-cn.pdf, citation=cs-cn.pdf:p21#cs-cn:p21:c003
- rank=2, score=0.339668, source=cs-cn.pdf, citation=cs-cn.pdf:p21#cs-cn:p21:c001
- rank=3, score=0.300485, source=cs-cn.pdf, citation=cs-cn.pdf:p21#cs-cn:p21:c002
