#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${KD_AGENT_PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
MODEL_NAME="qwen-8b-instruct-baseline"
MODELFILE="$PROJECT_ROOT/configs/Modelfile.baseline"
OLLAMA_MODEL_DIR="$PROJECT_ROOT/models/ollama"

export OLLAMA_MODELS="$OLLAMA_MODEL_DIR"

cd "$PROJECT_ROOT"
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
