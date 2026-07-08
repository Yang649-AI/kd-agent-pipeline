# Project Context

## Repository

- GitHub: `https://github.com/Yang649-AI/kd-agent-pipeline`
- Local path: `D:\program\code\Python\kd-agent-pipeline`
- Remote-tracking branches currently used:
  - `main`
  - `feature/system-pipeline`
- Local deployment branch:
  - `local/windows-deploy`

Use `main` and `feature/system-pipeline` as clean mirrors of the server-side repository. Keep Windows/local deployment changes on `local/windows-deploy`.

## Local Conda Environment

The local GPU environment is already installed:

```powershell
conda activate kd-agent-pipeline-gpu
```

Verified package state:

- Python `3.11.15`
- PyTorch `2.12.1`
- `torch.cuda.is_available()` returns `True`
- Core dependencies import successfully:
  - `langchain`
  - `langchain_core`
  - `langchain_community`
  - `langchain_chroma`
  - `langchain_huggingface`
  - `langchain_ollama`
  - `chromadb`
  - `sentence_transformers`
  - `fitz`
  - `pandas`
  - `numpy`
  - `tqdm`
  - `transformers`
  - `accelerate`

The environment is stored under:

```text
D:\program\tool\anaconda\envs\kd-agent-pipeline-gpu
```

## Environment Variables

Python scripts now resolve the project root through `KD_AGENT_PROJECT_ROOT` first, then auto-detect the repository root.

Recommended local PowerShell setup:

```powershell
cd D:\program\code\Python\kd-agent-pipeline
conda activate kd-agent-pipeline-gpu
$env:KD_AGENT_PROJECT_ROOT="D:\program\code\Python\kd-agent-pipeline"
```

Optional variables:

```powershell
$env:KD_AGENT_CONDA_ENV="kd-agent-pipeline-gpu"
$env:KD_AGENT_OLLAMA_MODELS="D:\program\code\Python\kd-agent-pipeline\models\ollama"
$env:KD_AGENT_BASELINE_GGUF="D:\program\code\Python\kd-agent-pipeline\models\gguf\Qwen3-8B-Q4_K_M.gguf"
$env:KD_AGENT_SYSTEM_GGUF="D:\program\code\Python\kd-agent-pipeline\models\gguf\Qwen3-VL-8B.gguf"
```

## Local Path Adaptation

The old server path `/root/autodl-tmp/kd_agent_pipeline` has been removed from Python and shell entrypoints on `local/windows-deploy`.

The shared Python path resolver is:

```text
src/common/paths.py
```

It exposes:

```python
from common.paths import PROJECT_ROOT
```

Use that helper for any new Python scripts that need project-relative paths.

## Long-Term Update Workflow

Use this workflow when the GitHub repository updates:

```powershell
cd D:\program\code\Python\kd-agent-pipeline

git fetch origin

git checkout main
git pull --ff-only origin main

git checkout feature/system-pipeline
git pull --ff-only origin feature/system-pipeline

git checkout local/windows-deploy
git rebase feature/system-pipeline
```

If a rebase conflicts, resolve only the local deployment differences. The common conflict areas are expected to be path handling, shell startup scripts, README setup instructions, and documentation files.

## Known Local Git Notes

This repository may trigger Git safe-directory warnings because Codex and the normal Windows user can own different parts of the working tree.

The expected safe-directory config is:

```powershell
git config --global --add safe.directory D:/program/code/Python/kd-agent-pipeline
```

If GitHub access fails with `Recv failure: Connection was reset`, check local proxy variables:

```powershell
Get-ChildItem Env: | Where-Object { $_.Name -match 'proxy' }
git ls-remote origin
```

Temporarily clear proxy variables in the current terminal if needed:

```powershell
$env:ALL_PROXY=''
$env:HTTP_PROXY=''
$env:HTTPS_PROXY=''
git fetch origin
```

## Current Caveats

- `.idea/` and `configs/.idea/` are untracked local IDE directories.
- The repository contains some mojibake text in prompts and generated report templates from upstream history. This local deployment pass does not rewrite those strings.
- Data files under `data/raw/`, local model files under `models/`, generated outputs, and caches should remain untracked.

