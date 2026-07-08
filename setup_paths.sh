#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_ROOT="${KD_AGENT_PROJECT_ROOT:-$SCRIPT_DIR}"

export PIP_CACHE_DIR=$PROJECT_ROOT/cache/pip

export HF_HOME=$PROJECT_ROOT/cache/huggingface
export TRANSFORMERS_CACHE=$PROJECT_ROOT/cache/huggingface/transformers
export HF_DATASETS_CACHE=$PROJECT_ROOT/cache/huggingface/datasets
export SENTENCE_TRANSFORMERS_HOME=$PROJECT_ROOT/cache/huggingface/sentence_transformers

export TORCH_HOME=$PROJECT_ROOT/cache/torch
export TMPDIR=$PROJECT_ROOT/cache/tmp

export OLLAMA_MODELS=$PROJECT_ROOT/models/ollama

echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "PIP_CACHE_DIR=$PIP_CACHE_DIR"
echo "HF_HOME=$HF_HOME"
echo "OLLAMA_MODELS=$OLLAMA_MODELS"

# Hugging Face mirror for model download
export HF_ENDPOINT=https://hf-mirror.com
