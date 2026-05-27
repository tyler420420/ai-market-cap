@echo off
REM AI Market Cap Tracker - Auto-restart wrapper
cd /d %~dp0
:loop
    python tracker.py
    echo.
    echo [WRAPPER] Tracker exited at %TIME%, restarting in 60s...
    timeout /t 60 /nobreak >nul
    goto loop