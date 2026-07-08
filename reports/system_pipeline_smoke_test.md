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

- Total text chunks: 2906
- High-quality chunks: 1603
- Low-quality chunks: 1303
- OCR todo pages: 421

### Content Role Distribution

| Content role | Count |
|---|---:|
| explanatory_text | 1533 |
| figure_or_caption | 896 |
| exercise_or_problem | 371 |
| short_explanatory_text | 70 |
| table_or_layout_fragment | 36 |

### Low-quality Reason Distribution

| Reason | Count |
|---|---:|
| explanatory_rescue | 1247 |
| figure_like_content | 991 |
| exercise_like_content | 371 |
| table_like_content | 51 |
| too_short | 3 |
| low_alpha_ratio | 3 |
| digit_ratio_high | 3 |

## 4. System RAG Smoke Test Summary

- Total questions: 4
- Answered questions: 4
- Not-found answers: 0
- Average retrieved chunks per question: 4.00

### Retrieved Source Distribution

| Source file | Retrieved count |
|---|---:|
| cs-eg.pdf | 16 |

## 5. Question-level Results

| ID | Question | Answer status | Retrieved chunks | First citation |
|---|---|---|---:|---|
| cs_eg_001 | What is virtual memory in computer systems? | answered | 4 | cs-eg.pdf#page=909 |
| cs_eg_002 | What is a process in an operating system? | answered | 4 | cs-eg.pdf#page=701 |
| cs_eg_003 | What is cache memory? | answered | 4 | cs-eg.pdf#page=671 |
| cs_eg_004 | What is exceptional control flow? | answered | 4 | cs-eg.pdf#page=810 |

## 6. Notes

- The current system RAG runner is used for pipeline validation. The formal target base model is Qwen3-VL-8B, as recorded in `configs/system_config.yaml`.
- Chunk quality fields are preserved in metadata, including `quality_score`, `is_low_quality`, `quality_reasons`, and `content_role`.
- Scanned or image-only PDF pages are recorded in the OCR todo list for later multimodal or OCR processing.
