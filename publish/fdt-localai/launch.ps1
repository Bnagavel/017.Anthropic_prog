<#
.SYNOPSIS
    F&DT-LocalAI (Release 1.0) Launcher & Health Check Script (ARCHITECTURE.md §7)
.DESCRIPTION
    Manages the local UI server and verifies offline environment variables on 127.0.0.1.
#>
param(
    [ValidateSet("start", "status", "cli-demo")]
    [string]$Action = "start",
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

$env:OLLAMA_HOST = "127.0.0.1:11434"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:PYTHONPATH = Join-Path $RootDir "src"

if ($Action -eq "status") {
    Write-Host "[F&DT-LocalAI] Offline Mode: ENABLED (Bind: 127.0.0.1)" -ForegroundColor Green
    Write-Host "[F&DT-LocalAI] Checking Python 3.12 environment..."
    py -3.12 --version
    exit 0
}

if ($Action -eq "cli-demo") {
    Write-Host "[F&DT-LocalAI] Running example pipeline via CLI..." -ForegroundColor Cyan
    py -3.12 -m fdt_localai.cli run "Spectrum\example" --base-name "SPECTRUM" --ai-summary
    exit 0
}

Write-Host "[F&DT-LocalAI] Starting Simple Excel-Form UI at http://127.0.0.1:$Port ..." -ForegroundColor Green
py -3.12 ui_app.py
