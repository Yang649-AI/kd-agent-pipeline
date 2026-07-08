#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${KD_AGENT_PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
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
if [[ "$FROM_PATH" != /* ]]; then
  FROM_PATH="$PROJECT_ROOT/${FROM_PATH#./}"
fi

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
