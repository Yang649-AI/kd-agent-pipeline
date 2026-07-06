# Raw PDF 清洗后计算机教材评测记录

## 数据源

- `cs-cn.pdf`：扫描/图片版，进入 OCR todo，暂未参与文本检索。
- `cs-eg.pdf`：英文 CSAPP 教材，使用原系统清洗后的高质量文本 chunk 参与检索。

## 指标

- 原始 chunk 数：2875
- 入索引高质量 chunk 数：1572
- OCR todo 页：{'cs-cn.pdf': 441, 'cs-eg.pdf': 8}
- 测试问题数：5
- 平均答案关键词召回：46.67%
- 无引用生成/幻觉率：0.00%
- 平均延迟：0.0044 s
- 平均总 Token：529.00
- 平均上下文压缩比例：53.97%

## 样例结果

### raw_cs_001

问题：What is virtual memory and what capabilities does it provide?

回答：In order to manage memory more efficiently and with fewer errors, modern systems provide an abstraction of main memory known as virtual memory (VM). [S1] Virtual memory is an elegant interaction of hardware exceptions, hardware ad- dress translation, main memory, disk files, and kernel software that provides each process with a large, uniform, and private address space. [S1] With one clean mech- anism, virtual memory provides three important capabilities: (1) It uses main memory efficiently by treating it as a cache for an address space stored on disk, keeping only the active areas in main memory and transferring data back and forth between disk and memory as needed. [S1]

关键词召回：33.33%

检索来源：
- rank=1, score=0.193345, source=cs-eg.pdf, page=cs-eg.pdf:p836#cs_cs-eg_pdf_p836_c1, chunk=cs_cs-eg_pdf_p836_c1
- rank=2, score=0.167173, source=cs-eg.pdf, page=cs-eg.pdf:p68#cs_cs-eg_pdf_p68_c3, chunk=cs_cs-eg_pdf_p68_c3
- rank=3, score=0.160922, source=cs-eg.pdf, page=cs-eg.pdf:p836#cs_cs-eg_pdf_p836_c3, chunk=cs_cs-eg_pdf_p836_c3

### raw_cs_002

问题：What is Amdahl's law and how does it limit total speedup?

回答：only 80% of the system can be improved.' How much (i.e., what value of k) would you need to improve this part to meet the overall performance target? [S1] , One interesting SP\'!'ial case of Amdahl's law is to c9nsider the effect of setting k to oo. [S1] That is, we are able to take some part of the system and speed it up to the point.at which it takes I\ negligibl<; ~ount of time. [S1]

关键词召回：33.33%

检索来源：
- rank=1, score=0.241178, source=cs-eg.pdf, page=cs-eg.pdf:p57#cs_cs-eg_pdf_p57_c1, chunk=cs_cs-eg_pdf_p57_c1
- rank=2, score=0.199948, source=cs-eg.pdf, page=cs-eg.pdf:p602#cs_cs-eg_pdf_p602_c2, chunk=cs_cs-eg_pdf_p602_c2
- rank=3, score=0.183071, source=cs-eg.pdf, page=cs-eg.pdf:p56#cs_cs-eg_pdf_p56_c1, chunk=cs_cs-eg_pdf_p56_c1

### raw_cs_003

问题：How do temporal locality and spatial locality relate to the memory hierarchy?

回答：xxiv Preface [S1] Chapter 6: The Memory Hierarchy. [S1] The memory system is one of the most visible parts of a computer system to application programmers. [S1]

关键词召回：0.00%

检索来源：
- rank=1, score=0.305976, source=cs-eg.pdf, page=cs-eg.pdf:p22#cs_cs-eg_pdf_p22_c0, chunk=cs_cs-eg_pdf_p22_c0
- rank=2, score=0.283023, source=cs-eg.pdf, page=cs-eg.pdf:p642#cs_cs-eg_pdf_p642_c0, chunk=cs_cs-eg_pdf_p642_c0
- rank=3, score=0.277066, source=cs-eg.pdf, page=cs-eg.pdf:p669#cs_cs-eg_pdf_p669_c1, chunk=cs_cs-eg_pdf_p669_c1

### raw_cs_004

问题：What is exceptional control flow in a computer system?

回答：Bibliographic Notes [S3] 8.8 Summary Exceptional control flow (ECF) occurs at all levels of a computer system and is a basic mechanism for providing concurrency in a computer system .. [S3] At the hardware level, exceptions are abrupt changes in the control flow that are triggered by events in the processor. [S3]

关键词召回：100.00%

检索来源：
- rank=1, score=0.311032, source=cs-eg.pdf, page=cs-eg.pdf:p22#cs_cs-eg_pdf_p22_c2, chunk=cs_cs-eg_pdf_p22_c2
- rank=2, score=0.256723, source=cs-eg.pdf, page=cs-eg.pdf:p770#cs_cs-eg_pdf_p770_c0, chunk=cs_cs-eg_pdf_p770_c0
- rank=3, score=0.242685, source=cs-eg.pdf, page=cs-eg.pdf:p821#cs_cs-eg_pdf_p821_c0, chunk=cs_cs-eg_pdf_p821_c0

### raw_cs_005

问题：What is a process virtual address space?

回答：In order to manage memory more efficiently and with fewer errors, modern systems provide an abstraction of main memory known as virtual memory (VM). [S2] Virtual memory is an elegant interaction of hardware exceptions, hardware ad- dress translation, main memory, disk files, and kernel software that provides each process with a large, uniform, and private address space. [S2] With one clean mech- anism, virtual memory provides three important capabilities: (1) It uses main memory efficiently by treating it as a cache for an address space stored on disk, keeping only the active areas in main memory and transferring data back and forth between disk and memory as needed. [S2]

关键词召回：66.67%

检索来源：
- rank=1, score=0.27743, source=cs-eg.pdf, page=cs-eg.pdf:p838#cs_cs-eg_pdf_p838_c1, chunk=cs_cs-eg_pdf_p838_c1
- rank=2, score=0.260683, source=cs-eg.pdf, page=cs-eg.pdf:p836#cs_cs-eg_pdf_p836_c1, chunk=cs_cs-eg_pdf_p836_c1
- rank=3, score=0.239341, source=cs-eg.pdf, page=cs-eg.pdf:p68#cs_cs-eg_pdf_p68_c3, chunk=cs_cs-eg_pdf_p68_c3

## 结论

使用清洗后的高质量 chunk 后，英文教材检索与引用链路可以跑通；中文教材需要 OCR 后才能做同等评测。