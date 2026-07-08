# Agent Instructions

## Scope

This workspace is a local Windows deployment of `Yang649-AI/kd-agent-pipeline`.

The active local deployment branch should be:

```text
local/windows-deploy
```

Do not make local Windows deployment edits directly on `main` or `feature/system-pipeline`. Those branches are used to mirror the server-side GitHub repository.

## Repository And Environment

- Workspace: `D:\program\code\Python\kd-agent-pipeline`
- Conda environment: `kd-agent-pipeline-gpu`
- Conda env path: `D:\program\tool\anaconda\envs\kd-agent-pipeline-gpu`
- Python version: `3.11.15`
- PyTorch version: `2.12.1`
- CUDA availability was verified as `True`.

Before running Python commands locally:

```powershell
cd D:\program\code\Python\kd-agent-pipeline
conda activate kd-agent-pipeline-gpu
$env:KD_AGENT_PROJECT_ROOT="D:\program\code\Python\kd-agent-pipeline"
```

## Path Handling

Do not reintroduce hardcoded server paths such as:

```text
/root/autodl-tmp/kd_agent_pipeline
```

Python entrypoints should use:

```python
from common.paths import PROJECT_ROOT
```

The implementation lives in:

```text
src/common/paths.py
```

Shell scripts should respect these environment variables:

- `KD_AGENT_PROJECT_ROOT`
- `KD_AGENT_CONDA_ENV`
- `KD_AGENT_OLLAMA_MODELS`
- `KD_AGENT_BASELINE_GGUF`
- `KD_AGENT_SYSTEM_GGUF`

## Branch Maintenance

When the upstream repository changes, update in this order:

```powershell
git fetch origin

git checkout main
git pull --ff-only origin main

git checkout feature/system-pipeline
git pull --ff-only origin feature/system-pipeline

git checkout local/windows-deploy
git rebase feature/system-pipeline
```

If conflicts occur, preserve local environment-variable path support and avoid changing upstream algorithmic behavior unless the user explicitly asks.

## Verification Commands

Quick import verification:

```powershell
& "D:\program\tool\anaconda\envs\kd-agent-pipeline-gpu\python.exe" -c "import torch, langchain, chromadb, sentence_transformers, fitz; print(torch.__version__); print(torch.cuda.is_available())"
```

Path helper verification:

```powershell
& "D:\program\tool\anaconda\envs\kd-agent-pipeline-gpu\python.exe" -c "import sys; sys.path.insert(0, r'D:\program\code\Python\kd-agent-pipeline\src'); from common.paths import PROJECT_ROOT; print(PROJECT_ROOT)"
```

Syntax check for changed Python files:

```powershell
& "D:\program\tool\anaconda\envs\kd-agent-pipeline-gpu\python.exe" -m compileall scripts src
```

## Local Files

The following local directories may exist and should not be committed unless the user explicitly asks:

- `.idea/`
- `configs/.idea/`
- `cache/`
- `models/`
- `outputs/`
- `data/raw/`
- `data/indexes/`
- `data/processed/`

## Style Notes

Keep changes small and local to the deployment problem. This branch exists to make the server-origin project run locally on Windows while remaining easy to rebase when upstream updates.

