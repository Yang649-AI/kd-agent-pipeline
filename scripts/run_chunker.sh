#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${KD_AGENT_PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CONDA_ENV="${KD_AGENT_CONDA_ENV:-kd-agent-pipeline-gpu}"

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
