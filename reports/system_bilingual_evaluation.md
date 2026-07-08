# 正式 Qwen3-VL 双语系统评测报告

## 评测设置

- 正式模型：`qwen3-vl-8b-system`（基于 `Qwen3-VL-8B-Instruct-Q4_K_M.gguf` 构建）
- 检索索引：Chroma `system_rag`
- 检索数据：中文 OCR 教材 `cs-cn.pdf` + 英文文本教材 `cs-eg.pdf`
- 评测集：`data/eval/cs_bilingual_questions.jsonl`
- 输出结果：`outputs/system/system_bilingual_results.jsonl`
- 检索策略：向量召回 top20 候选 + 双语术语扩展 + 关键词/OCR 兜底召回 + top5 重排

## 指标

| 指标 | 结果 |
| --- | ---: |
| 测试问题数 | 8 |
| 回答语言匹配率 | 100.00% |
| 准确率/平均答案关键词召回 | 91.67% |
| 幻觉率/无证据回答率 | 0.00% |
| Hit@5 | 100.00% |
| 平均延迟 | 2.10 s |
| 中位延迟 | 2.18 s |
| 估算吞吐 | 约 1900.64 token/s |
| 平均输入 Token | 3568.88 |
| 平均输出 Token | 421.25 |
| 平均总 Token | 3990.13 |
| 总 Token | 31921 |

说明：Qwen3-VL tokenizer 未缓存到本地，本轮 Token 统计仍使用脚本粗略估算。

## 检索来源

| 来源文件 | 被检索次数 |
| --- | ---: |
| `cs-cn.pdf` | 18 |
| `cs-eg.pdf` | 22 |

## 结论

本轮正式系统已经同时纳入中文 OCR 教材和英文教材。中文问题均以中文回答，英文问题均以英文回答；跨语言问题也能根据另一语言教材证据作答。`zh_ml_002` 通过关键词/OCR 兜底召回补入 `cs-cn.pdf` 中“查准率、查全率”相关页面，解决了纯向量召回无法命中 OCR chunk 的问题。
