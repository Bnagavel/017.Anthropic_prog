@echo off
setlocal
cd /d "%~dp0"

echo ===================================================
echo   AutoHex Daily Loop - DRY RUN (Discord Gate Test)
echo ===================================================

if not exist ".env" (
    echo [NOTE] .env file not found in %~dp0
    echo        Running with local console fallback unless environment variables are set.
    echo.
)

python daily_orchestrator.py --dry-run

echo.
pause
