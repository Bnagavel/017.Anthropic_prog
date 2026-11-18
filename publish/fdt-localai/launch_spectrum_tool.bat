@echo off
REM ============================================================================
REM F&DT Spectrum Assistant (Release 1.0) - One-Click Offline Windows Launcher
REM Strictly bound to 127.0.0.1 (100% Air-Gapped Local Execution)
REM ============================================================================
setlocal
cd /d "%~dp0"

set OLLAMA_HOST=127.0.0.1:11434
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
set PYTHONPATH=%~dp0src

echo ============================================================================
echo  F^&DT Spectrum Assistant (Release 1.0) - Offline Spectrum Engine
echo  Binding strictly to http://127.0.0.1:8501 (Zero External Network Access)
echo ============================================================================

start "" http://127.0.0.1:8501
py -3.12 "%~dp0ui_app.py"
if %ERRORLEVEL% NEQ 0 (
    python "%~dp0ui_app.py"
)
pause
