#!/usr/bin/env bash
set -e

PROJECT_ROOT="/root/autodl-tmp/kd_agent_pipeline"
CONDA_ENV="$PROJECT_ROOT/envs/kd_agent"

cd "$PROJECT_ROOT"

source "$PROJECT_ROOT/setup_paths.sh"

if [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
  source ~/miniconda3/etc/profile.d/conda.sh
fi

conda activate "$CONDA_ENV"

echo "Building system vector index..."
INCLUDE_LOW_QUALITY=1 python src/indexer/build_system_index.py

echo "System vector index finished."
echo "Index path: $PROJECT_ROOT/data/indexes/chroma_system"
