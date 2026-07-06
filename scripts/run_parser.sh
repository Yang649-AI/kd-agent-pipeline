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

echo "Running PDF parser..."
python src/parser/parse_pdf_pages.py

echo "PDF parsing finished."
echo "Parsed result path:"
echo "$PROJECT_ROOT/data/processed/parsed_pages.jsonl"
