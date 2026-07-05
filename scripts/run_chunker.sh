#!/usr/bin/env bash
set -e

PROJECT_ROOT="/root/autodl-tmp/kd_agent_pipeline"
CONDA_ENV="$PROJECT_ROOT/envs/kd_agent"

cd "$PROJECT_ROOT"

source "$PROJECT_ROOT/setup_paths.sh"

if [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
  source ~/miniconda3/etc/profile.d/conda.sh
fi

conda activate "$CONDA_ENV"

echo "Building text chunks..."
python src/chunker/build_text_chunks.py

echo "Chunking finished."
echo "Text chunks: $PROJECT_ROOT/data/processed/text_chunks.jsonl"
echo "OCR todo pages: $PROJECT_ROOT/data/processed/ocr_todo_pages.jsonl"
