#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$PROJECT_ROOT"

export PROJECT_ROOT
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

echo "Building KD agent index..."
python scripts/10_build_kd_agent_index.py

echo "Running CS evaluation..."
python scripts/11_run_kd_agent_eval.py

echo "Generating evaluation report..."
python scripts/12_generate_kd_agent_report.py

echo "KD agent pipeline finished."
