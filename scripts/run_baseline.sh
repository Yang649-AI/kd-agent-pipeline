#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${KD_AGENT_PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CONDA_ENV="$PROJECT_ROOT/envs/kd_agent"
OLLAMA_MODEL_DIR="$PROJECT_ROOT/models/ollama"

cd "$PROJECT_ROOT"

source "$PROJECT_ROOT/setup_paths.sh"

PYTHON_BIN="${PYTHON_BIN:-python}"
if [ -d "$CONDA_ENV" ] && [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
  source ~/miniconda3/etc/profile.d/conda.sh
  conda activate "$CONDA_ENV"
fi

export OLLAMA_MODELS="$OLLAMA_MODEL_DIR"

mkdir -p logs

if ! pgrep -f "ollama serve" >/dev/null 2>&1; then
  echo "Starting Ollama service..."
  nohup ollama serve > logs/ollama.log 2>&1 &
  sleep 5
fi

echo "Building baseline index..."
"$PYTHON_BIN" scripts/01_build_baseline_index.py

echo "Running baseline QA..."
"$PYTHON_BIN" scripts/02_run_baseline.py

echo "Calculating baseline metrics..."
"$PYTHON_BIN" scripts/03_calc_baseline_metrics.py

echo "Generating baseline report..."
"$PYTHON_BIN" scripts/04_generate_baseline_report.py

echo "Baseline pipeline finished."
