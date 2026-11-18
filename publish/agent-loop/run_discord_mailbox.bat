@echo off
setlocal
cd /d "%~dp0"

:loop
echo ==========================================================
echo   AutoHex Discord Mailbox Relay (24/7 Continuous Loop)
echo ==========================================================

python discord_mailbox.py
set RET_CODE=%ERRORLEVEL%

if %RET_CODE% EQU 42 (
    echo.
    echo [RELAY] Stopped cleanly by user command (STOP/EXIT).
    pause
    goto end
)

echo.
echo [RELAY] Relay process exited (code %RET_CODE%). Restarting in 2 seconds...
timeout /t 2 >nul
goto loop

:end
