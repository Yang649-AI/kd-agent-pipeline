#!/usr/bin/env bash
set -e

PROJECT_ROOT="/root/autodl-tmp/kd_agent_pipeline"
MODEL_NAME="qwen-8b-instruct-baseline"
MODELFILE="$PROJECT_ROOT/configs/Modelfile.baseline"
OLLAMA_MODEL_DIR="$PROJECT_ROOT/models/ollama"

export OLLAMA_MODELS="$OLLAMA_MODEL_DIR"

echo "Project root: $PROJECT_ROOT"
echo "Ollama model dir: $OLLAMA_MODELS"
echo "Model name: $MODEL_NAME"

if ! command -v ollama >/dev/null 2>&1; then
  echo "ERROR: ollama command not found."
  exit 1
fi

if [ ! -f "$MODELFILE" ]; then
  echo "ERROR: Modelfile not found: $MODELFILE"
  exit 1
fi

echo "Creating Ollama model..."
ollama create "$MODEL_NAME" -f "$MODELFILE"

echo "Ollama model list:"
ollama list

echo "Done."
