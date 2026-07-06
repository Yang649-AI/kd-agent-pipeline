#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${KD_AGENT_PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CONDA_ENV="${KD_AGENT_CONDA_ENV:-kd-agent-pipeline-gpu}"
OLLAMA_MODEL_DIR="${KD_AGENT_OLLAMA_MODELS:-$PROJECT_ROOT/models/ollama}"

cd "$PROJECT_ROOT"

source "$PROJECT_ROOT/setup_paths.sh"

if [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
  source ~/miniconda3/etc/profile.d/conda.sh
fi

conda activate "$CONDA_ENV"

export OLLAMA_MODELS="$OLLAMA_MODEL_DIR"

mkdir -p logs

if ! pgrep -f "ollama serve" >/dev/null 2>&1; then
  echo "Starting Ollama service..."
  nohup ollama serve > logs/ollama.log 2>&1 &
  sleep 5
fi

echo "Building baseline index..."
python scripts/01_build_baseline_index.py

echo "Running baseline QA..."
python scripts/02_run_baseline.py

echo "Calculating baseline metrics..."
python scripts/03_calc_baseline_metrics.py

echo "Generating baseline report..."
python scripts/04_generate_baseline_report.py

echo "Baseline pipeline finished."
