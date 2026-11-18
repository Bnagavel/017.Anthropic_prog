@echo off
setlocal
cd /d "%~dp0"

echo ===================================================
echo   AutoHex Daily Loop - LIVE EXECUTION
echo ===================================================

python daily_orchestrator.py %*

echo.
pause
