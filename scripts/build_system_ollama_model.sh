#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${KD_AGENT_PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
MODEL_NAME="${KD_AGENT_SYSTEM_MODEL_NAME:-qwen3-vl-8b-system}"
MODEL_FILE="$PROJECT_ROOT/configs/Modelfile.system"
BASE_MODEL_PATH="${KD_AGENT_SYSTEM_GGUF:-$PROJECT_ROOT/models/gguf/Qwen3-VL-8B.gguf}"
OLLAMA_MODEL_DIR="${KD_AGENT_OLLAMA_MODELS:-$PROJECT_ROOT/models/ollama}"
GENERATED_MODELFILE="$PROJECT_ROOT/cache/ollama/Modelfile.system.local"

export OLLAMA_MODELS="$OLLAMA_MODEL_DIR"

cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"
echo "Ollama model dir: $OLLAMA_MODELS"
echo "Model name: $MODEL_NAME"
echo "Modelfile: $MODEL_FILE"
echo "Base model: $BASE_MODEL_PATH"

if [ ! -f "$MODEL_FILE" ]; then
  echo "ERROR: Modelfile not found: $MODEL_FILE"
  exit 1
fi

echo "Checking FROM model path in Modelfile..."

if [ ! -f "$BASE_MODEL_PATH" ]; then
  echo "ERROR: Base model file not found:"
  echo "$BASE_MODEL_PATH"
  echo ""
  echo "Please download or convert the Qwen3-VL-8B Ollama-compatible model first,"
  echo "or set KD_AGENT_SYSTEM_GGUF to its local path."
  exit 1
fi

mkdir -p "$(dirname "$GENERATED_MODELFILE")"
awk -v from_path="$BASE_MODEL_PATH" '
  /^FROM / && !replaced { print "FROM " from_path; replaced=1; next }
  { print }
' "$MODEL_FILE" > "$GENERATED_MODELFILE"

echo "Building Ollama model..."
ollama create "$MODEL_NAME" -f "$GENERATED_MODELFILE"

echo "Done."
echo "You can test it with:"
echo "ollama run $MODEL_NAME"
