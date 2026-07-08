param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Question
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$CondaEnv = "D:\program\tool\anaconda\envs\kd-agent-pipeline-gpu"
$PythonExe = Join-Path $CondaEnv "python.exe"
$QuestionText = ($Question -join " ").Trim()

if (-not $QuestionText) {
    $QuestionText = Read-Host "Power PMAC question"
}

if (-not $QuestionText) {
    throw "Question cannot be empty."
}

$env:KD_AGENT_PROJECT_ROOT = $ProjectRoot
$env:NO_PROXY = "localhost,127.0.0.1,::1"
$env:no_proxy = "localhost,127.0.0.1,::1"
$env:PYTHONIOENCODING = "utf-8"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:HF_DATASETS_OFFLINE = "1"
$env:HF_HUB_DISABLE_TELEMETRY = "1"
$env:PATH = "$CondaEnv\Library\bin;$CondaEnv\Scripts;$CondaEnv;$env:PATH"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$OutputPath = Join-Path $ProjectRoot "outputs\system\manual_power_pmac_results.jsonl"
$AskScript = Join-Path $ProjectRoot "src\agent\ask_system_once.py"

& $PythonExe $AskScript --output $OutputPath --question $QuestionText
