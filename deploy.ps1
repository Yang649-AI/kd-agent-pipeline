$ErrorActionPreference = "Stop"

$ProjectRoot = if ($env:PROJECT_ROOT) { $env:PROJECT_ROOT } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
Set-Location $ProjectRoot
$env:PROJECT_ROOT = $ProjectRoot
$env:PYTHONPATH = "$ProjectRoot;$env:PYTHONPATH"

python scripts/10_build_kd_agent_index.py
python scripts/11_run_kd_agent_eval.py
python scripts/12_generate_kd_agent_report.py
