#!/usr/bin/env bash
set -e

PROJECT_ROOT="/root/autodl-tmp/kd_agent_pipeline"
MODEL_NAME="qwen3-vl-8b-system"
MODEL_FILE="$PROJECT_ROOT/configs/Modelfile.system"
OLLAMA_MODEL_DIR="$PROJECT_ROOT/models/ollama"

export OLLAMA_MODELS="$OLLAMA_MODEL_DIR"

cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"
echo "Ollama model dir: $OLLAMA_MODELS"
echo "Model name: $MODEL_NAME"
echo "Modelfile: $MODEL_FILE"

if [ ! -f "$MODEL_FILE" ]; then
  echo "ERROR: Modelfile not found: $MODEL_FILE"
  exit 1
fi

echo "Checking FROM model path in Modelfile..."
FROM_PATH=$(grep "^FROM " "$MODEL_FILE" | awk '{print $2}')

if [ ! -f "$FROM_PATH" ]; then
  echo "ERROR: Base model file not found:"
  echo "$FROM_PATH"
  echo ""
  echo "Please download or convert the Qwen3-VL-8B Ollama-compatible model first,"
  echo "then update configs/Modelfile.system."
  exit 1
fi

echo "Building Ollama model..."
ollama create "$MODEL_NAME" -f "$MODEL_FILE"

echo "Done."
echo "You can test it with:"
echo "ollama run $MODEL_NAME"
