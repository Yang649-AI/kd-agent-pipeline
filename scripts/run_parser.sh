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

echo "Running PDF parser..."
python src/parser/parse_pdf_pages.py

echo "PDF parsing finished."
echo "Parsed result path:"
echo "$PROJECT_ROOT/data/processed/parsed_pages.jsonl"
