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

echo "Running PDF parser..."
"$PYTHON_BIN" src/parser/parse_pdf_pages.py

echo "PDF parsing finished."
echo "Parsed result path:"
echo "$PROJECT_ROOT/data/processed/parsed_pages.jsonl"
