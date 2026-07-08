#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${KD_AGENT_PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CONDA_ENV="$PROJECT_ROOT/envs/kd_agent"

cd "$PROJECT_ROOT"

source "$PROJECT_ROOT/setup_paths.sh"

PYTHON_BIN="${PYTHON_BIN:-python}"
if [ -d "$CONDA_ENV" ] && [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
  source ~/miniconda3/etc/profile.d/conda.sh
  conda activate "$CONDA_ENV"
fi

echo "Building text chunks..."
"$PYTHON_BIN" src/chunker/build_text_chunks.py

echo "Chunking finished."
echo "Text chunks: $PROJECT_ROOT/data/processed/text_chunks.jsonl"
echo "OCR todo pages: $PROJECT_ROOT/data/processed/ocr_todo_pages.jsonl"
