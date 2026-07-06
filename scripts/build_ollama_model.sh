#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${KD_AGENT_PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
MODEL_NAME="${KD_AGENT_BASELINE_MODEL_NAME:-qwen-8b-instruct-baseline}"
MODELFILE="$PROJECT_ROOT/configs/Modelfile.baseline"
BASE_MODEL_PATH="${KD_AGENT_BASELINE_GGUF:-$PROJECT_ROOT/models/gguf/Qwen3-8B-Q4_K_M.gguf}"
OLLAMA_MODEL_DIR="${KD_AGENT_OLLAMA_MODELS:-$PROJECT_ROOT/models/ollama}"
GENERATED_MODELFILE="$PROJECT_ROOT/cache/ollama/Modelfile.baseline.local"

export OLLAMA_MODELS="$OLLAMA_MODEL_DIR"

echo "Project root: $PROJECT_ROOT"
echo "Ollama model dir: $OLLAMA_MODELS"
echo "Model name: $MODEL_NAME"
echo "Base model: $BASE_MODEL_PATH"

if ! command -v ollama >/dev/null 2>&1; then
  echo "ERROR: ollama command not found."
  exit 1
fi

if [ ! -f "$MODELFILE" ]; then
  echo "ERROR: Modelfile not found: $MODELFILE"
  exit 1
fi

if [ ! -f "$BASE_MODEL_PATH" ]; then
  echo "ERROR: Base model file not found: $BASE_MODEL_PATH"
  exit 1
fi

mkdir -p "$(dirname "$GENERATED_MODELFILE")"
awk -v from_path="$BASE_MODEL_PATH" '
  /^FROM / && !replaced { print "FROM " from_path; replaced=1; next }
  { print }
' "$MODELFILE" > "$GENERATED_MODELFILE"

echo "Creating Ollama model..."
ollama create "$MODEL_NAME" -f "$GENERATED_MODELFILE"

echo "Ollama model list:"
ollama list

echo "Done."
