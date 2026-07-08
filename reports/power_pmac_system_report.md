# System Pipeline Smoke Test Report

## 1. Purpose

This report summarizes the current formal system pipeline validation. The pipeline includes PDF parsing, text chunking, chunk quality annotation, system vector index construction, RAG retrieval, answer generation, and citation output.

## 2. Pipeline Components

| Module | File | Status |
|---|---|---|
| PDF parser | `src/parser/parse_pdf_pages.py` | Completed |
| Text chunker | `src/chunker/build_text_chunks.py` | Completed |
| System indexer | `src/indexer/build_system_index.py` | Completed |
| System RAG runner | `src/agent/run_system_rag.py` | Completed for smoke validation |
| System config | `configs/system_config.yaml` | Completed |
| System Modelfile template | `configs/Modelfile.system` | Completed |

## 3. Data Processing Summary

- Total text chunks: 4091
- High-quality chunks: 4055
- Low-quality chunks: 36
- OCR todo pages: 1

### Content Role Distribution

| Content role | Count |
|---|---:|
| explanatory_text | 3782 |
| short_explanatory_text | 287 |
| table_or_layout_fragment | 20 |
| weak_semantic_text | 2 |

### Low-quality Reason Distribution

| Reason | Count |
|---|---:|
| table_like_content | 20 |
| short_line_ratio_high | 14 |
| explanatory_rescue | 13 |
| avg_line_length_low | 12 |
| low_alpha_ratio | 6 |
| no_explanatory_sentence | 2 |
| digit_ratio_high | 2 |
| too_short | 1 |

## 4. System RAG Smoke Test Summary

- Total questions: 5
- Answered questions: 3
- Not-found answers: 2
- Average retrieved chunks per question: 4.00

### Retrieved Source Distribution

| Source file | Retrieved count |
|---|---:|
| Power PMAC Software Reference Manual.pdf | 20 |

## 5. Question-level Results

| ID | Question | Answer status | Retrieved chunks | First citation |
|---|---|---|---:|---|
| power_pmac_001 | What phone number is listed for Delta Tau Data Systems technical support? | answered | 4 | Power PMAC Software Reference Manual.pdf#page=1 |
| power_pmac_002 | In industrial applications, where should Delta Tau products be installed? | not_found | 4 | Power PMAC Software Reference Manual.pdf#page=375 |
| power_pmac_003 | When installing or handling Delta Tau products, what kind of materials should be avoided? | answered | 4 | Power PMAC Software Reference Manual.pdf#page=1 |
| power_pmac_004 | In the safety instructions, what does a Warning identify? | answered | 4 | Power PMAC Software Reference Manual.pdf#page=760 |
| power_pmac_005 | According to the safety instructions, what should never be disconnected or connected while the power source is energized? | not_found | 4 | Power PMAC Software Reference Manual.pdf#page=762 |

## 6. Notes

- The current system RAG runner is used for pipeline validation. The formal target base model is Qwen3-VL-8B, as recorded in `configs/system_config.yaml`.
- Chunk quality fields are preserved in metadata, including `quality_score`, `is_low_quality`, `quality_reasons`, and `content_role`.
- Scanned or image-only PDF pages are recorded in the OCR todo list for later multimodal or OCR processing.
