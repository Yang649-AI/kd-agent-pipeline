#!/usr/bin/env bash
set -e

PROJECT_ROOT="/root/autodl-tmp/kd_agent_pipeline"
CONDA_ENV="$PROJECT_ROOT/envs/kd_agent"
OLLAMA_MODEL_DIR="$PROJECT_ROOT/models/ollama"

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

echo "Running system RAG..."
python src/agent/run_system_rag.py

echo "System RAG finished."
echo "Result path: $PROJECT_ROOT/outputs/system/system_results.jsonl"
