# FY27 课题阶段测试报告：Power PMAC 知识智能体管线

生成日期：2026-07-08  
测试分支：`local/windows-deploy`  
项目方向：A「高效自动化知识蒸馏与智能体生成管线」

## 1. 报告目的

本报告根据当前 `kd-agent-pipeline` 在 Power PMAC 文档集上的测试结果，评估项目与 FY27 课题目标之间的对应关系。当前结果属于单学科、单领域的阶段性验证，重点验证：

- PDF 文档解析、分块、索引、检索、生成和引用输出是否形成闭环。
- 本地 Ollama + Qwen 8B 模型是否可用于垂直领域问答。
- 系统是否能在“有依据时回答、无依据时拒答”的规则下运行。
- 针对命令语法题和 ACC-24E3 硬件手册题的精确召回是否有改善。

本报告不是最终三学科正式验收报告；Hit@5、Token 效率相对基线、吞吐量等指标仍需要在正式评测集上继续补齐。

## 2. 课题目标对应关系

课题要求构建端到端的自动化知识蒸馏与智能体合成管线，将任意学科丛书转化为可本地运行的垂直领域智能体，并在消费级硬件上实现低资源、高效率、可复现部署。

| 课题目标 | 当前验证情况 | 阶段结论 |
|---|---|---|
| 文档解析到智能体问答闭环 | 已完成 PDF 解析、chunk 构建、Chroma 索引、Ollama 生成、引用输出 | 单学科 MVP 已跑通 |
| 本地 Ollama 部署 | 已使用 `qwen-8b-instruct-baseline` 通过 Ollama 回答问题 | 本地问答链路可用 |
| Citation Grounding | 输出包含 `source_file#page` 引用锚点；无依据时返回 `No supporting reference found` | 规则已生效 |
| 学科泛化 | 当前只验证 Power PMAC/ACC-24E3 文档 | 尚未满足三学科要求 |
| Hit@5 >= 85% | 目前只做了类别回答统计和重点召回检查 | 需要正式 ground truth 评测 |
| 无引用生成率 <= 15% | 反例题 5/5 正确拒答；但还未形成正式幻觉率脚本 | 方向正确，指标待补 |
| Token 效率 <= 基线 60% | 已记录平均 token，但未与 LangChain 标准 RAG 基线对比 | 待补基线实验 |
| 处理吞吐 >= 15 页/分钟 | 已记录解析页数和 chunk 数，但未生成吞吐报告 | 待补自动统计 |
| 一键部署成功率 100% | Windows 本地脚本已可运行，但仍依赖本机环境变量和 Ollama 服务 | 需继续封装 |

## 3. 测试环境与模型

| 项目 | 当前配置 |
|---|---|
| 操作系统 | Windows 本地环境 |
| Conda 环境 | `kd-agent-pipeline-gpu` |
| Python | 3.11.15 |
| PyTorch | 2.12.1 |
| CUDA | 已验证可用 |
| Embedding 模型 | `BAAI/bge-small-zh-v1.5` |
| 向量库 | Chroma，collection: `system_rag` |
| 生成模型 | Ollama 模型 `qwen-8b-instruct-baseline` |
| 单问入口 | `scripts/ask_power_pmac.ps1` |
| 系统单问实现 | `src/agent/ask_system_once.py` |

## 4. 测试数据与索引状态

当前索引包含 3 个 Power PMAC 相关 PDF：

| 文档 | 解析页数 | chunk 数 |
|---|---:|---:|
| `O015-E-01_Power PMAC Software Reference Manual.pdf` | 1706 | 4370 |
| `Power PMAC Software Reference Manual.pdf` | 1599 | 4091 |
| `_info_OMRON_Delta_Tau_ACC_24E3_Manual_2024314151533.pdf` | 178 | 496 |
| 合计 | 3483 | 8957 |

OCR 待处理页数：3 页，每个 PDF 各 1 页。当前 OCR fallback 尚未实现，这属于后续多模态解析能力的一部分。

## 5. 综合题集测试结果

测试文件：`outputs/system/power_pmac_question_set_results.jsonl`  
摘要报告：`reports/power_pmac_question_set_summary.md`

| 指标 | 结果 |
|---|---:|
| 总问题数 | 29 |
| 已回答 | 13 |
| 无依据拒答 | 16 |
| 反例题正确拒答 | 5/5 |
| `direct_extract` | 2 |
| `ollama` | 27 |
| 平均延迟 | 9.23 s |
| 平均总 Token | 3666.83 |

按题型统计：

| 题型 | 总数 | 已回答 | 无依据拒答 |
|---|---:|---:|---:|
| 精确事实题 | 5 | 3 | 2 |
| PMAC 命令语法题 | 5 | 1 | 4 |
| 数据结构题 | 5 | 5 | 0 |
| 软件手册版本区分题 | 4 | 3 | 1 |
| ACC-24E3 硬件题 | 5 | 1 | 4 |
| 反例题 | 5 | 0 | 5 |

### 5.1 已表现较好的能力

- 技术支持电话和邮箱可直接抽取，避免模型二次生成带来的格式错误。
- Power PMAC 数据结构题表现稳定，例如 `Motor[x].Servo.Kp`、`Motor[x].FatalFeLimit`、`Sys.ServoPeriod` 等问题均能基于引用回答。
- 跨版本联系信息对比可以召回 2019 与 2025 手册第一页，并生成对比式回答。
- 反例题全部拒答，包括医学、法律、Transformer、神经网络配置等文档外问题，说明 grounding 规则基本有效。

### 5.2 暴露出的主要问题

综合题集中的薄弱点集中在两类：

1. PMAC 命令语法题  
   初始测试中只有 `I{data}={expression}` 被正确回答，`I{data}->`、`undefine all`、`v`、`vers` 等命令召回不足。

2. ACC-24E3 硬件题  
   初始测试中部分问题被 Power PMAC 软件手册中的 `ACC24E3[i]` 软件寄存器内容干扰，硬件手册正文没有稳定排到前面。

这些问题不是 Ollama 服务故障，也不是模型不可用，而是检索阶段的候选证据不够精确。

## 6. 针对弱项的回归测试

针对上述问题，已在 `src/agent/ask_system_once.py` 增加两类检索增强：

- 命令语法精确召回：识别 `I{data}->`、`undefine all`、`v`、`vers` 等命令模式，并对正式 `Function/Syntax` 命令规格页加权。
- ACC-24E3 硬件手册优先召回：识别 `ACC-24E3` 查询，优先提升 `_info_OMRON_Delta_Tau_ACC_24E3_Manual_2024314151533.pdf`，并对目录页降权。

回归测试文件：`outputs/system/command_acc_recall_check.jsonl`

| 指标 | 结果 |
|---|---:|
| 回归问题数 | 8 |
| 已回答 | 8 |
| 无依据拒答 | 0 |
| `ollama` 模式 | 8 |
| 平均延迟 | 9.90 s |
| 平均总 Token | 3970.38 |

重点问题结果：

| 问题 | 结果摘要 | 关键引用 |
|---|---|---|
| `What does the I{data}-> command report?` | 报告指定 I-variable 的 definition | `O015-E-01...#page=1211` |
| `What is the function of the undefine all command?` | 清除所有坐标系的轴定义 | `O015-E-01...#page=1324` |
| `What does the v command report in Power PMAC?` | 报告指定 motor 或 coordinate system 的 actual velocity | `O015-E-01...#page=1324` |
| `What does the vers command return?` | 返回 firmware version string | `O015-E-01...#page=1326` |
| `What is the ACC-24E3 used for?` | 用于 UMAC rack 的轴接口、反馈处理和驱动/放大器命令 | `_info_OMRON...ACC_24E3...#page=8` |
| `How many channels of axis interface can ACC-24E3 provide?` | 2 或 4 个 axis interface channels | `_info_OMRON...ACC_24E3...#page=8` |
| `What types of amplifiers and drives can ACC-24E3 command?` | analog velocity-mode、analog torque-mode、direct-PWM、pulse-and-direction 等 | `_info_OMRON...ACC_24E3...#page=8/#page=14` |
| `What are the environmental specifications of ACC-24E3?` | 0°C to 55°C operating，-25°C to 70°C storage，10%-95% non-condensing humidity | `_info_OMRON...ACC_24E3...#page=9` |

阶段结论：针对命令语法和 ACC-24E3 硬件手册召回的专项改进有效，关键证据可以进入 top retrieved context，回答不再退化为 `No supporting reference found`。

## 7. 与课题验收指标的阶段性差距

| 验收项 | 当前状态 | 下一步补齐方式 |
|---|---|---|
| 三学科测试集 | 当前只有 Power PMAC 单领域 | 增加 CS/医学/法学或用户指定三类文档，每类 >=100 页 |
| Hit@5 | 目前未按 ground truth 自动计算 | 建立 `formal_ground_truth.jsonl`，实现 evidence page 命中统计 |
| 幻觉率 | 反例题人工统计 5/5 拒答 | 自动统计“无引用生成”和“引用不支持答案” |
| Token 效率 | 已记录平均 token，未做 baseline 对比 | 固定同一题集跑标准 RAG baseline，计算 system/baseline |
| 处理吞吐 | 已有页数/chunk 数，未记录总耗时 | 在 parser/chunker/indexer 中输出耗时和 pages/min |
| 一键部署 | 本地可运行，但仍需手动确认 Ollama、PATH、NO_PROXY | 封装 `deploy.ps1` 和健康检查脚本 |
| 多模态解析 | OCR todo 已记录，但 OCR fallback 未接入 | 实现 OCR 层并把 OCR 文本纳入 chunk/index |
| Qwen3-VL-8B | 当前使用 Qwen 8B 文本模型 | 后续接入 Qwen3-VL-8B GGUF/Modelfile |

## 8. 当前阶段结论

当前项目已经具备课题 A 方向的单学科 MVP 雏形：可以把 Power PMAC 领域 PDF 转为本地可问答的知识智能体，并输出可追溯引用。系统在数据结构题、精确联系方式、版本联系信息对比和反例拒答方面表现较好。

本轮测试最重要的发现是：系统质量瓶颈主要集中在检索召回，而不是 Ollama 或模型服务本身。针对命令语法和 ACC-24E3 硬件手册的词面召回与文档优先级调整后，专项回归题从原先的高比例拒答改善为 8/8 可回答。

从课题验收角度看，当前仍属于工程闭环验证阶段，尚未进入最终验收指标阶段。下一阶段应优先补齐正式评测体系，而不是继续盲目增加模型复杂度。

## 9. 下一步建议

1. 建立正式评测集  
   为 Power PMAC 当前 29 题补充 expected keywords 和 evidence pages，先把 Hit@5、关键词覆盖率、无引用生成率跑起来。

2. 重新运行 29 题完整题集  
   在命令语法和 ACC-24E3 召回增强后，重新生成 `power_pmac_question_set_results.jsonl`，观察整体回答数和各类别指标变化。

3. 增加 baseline 对比  
   使用“标准 RAG + Qwen-8B-Instruct”跑同一题集，计算 Token 消耗比、延迟差异和回答质量差异。

4. 做吞吐统计  
   在 PDF 解析、chunk、索引阶段记录耗时，生成 pages/min 和 chunks/min。

5. 封装一键健康检查  
   检查 Conda、CUDA、Ollama、模型名、Chroma 索引、`NO_PROXY`，降低本地部署门槛。

6. 扩展到三学科  
   在 Power PMAC 路线稳定后，再接入另外两个差异明显的学科文档，验证分块与检索策略是否泛化。

