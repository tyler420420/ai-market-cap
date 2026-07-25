@echo off
cd /d C:\Users\Tyler_AI\ai-market-cap

REM Run scanner locally (no finviz - fast)
"C:\Users\Tyler_AI\AppData\Local\Python\pythoncore-3.14-64\python.exe" ai_earnings_scanner.py --no-finviz
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Scanner failed
    exit /b 1
)

REM Copy fresh output to scanner.html (used by Flask web server)
copy /Y ai_earnings_today.html scanner.html >nul

REM Copy fresh output to Desktop shortcut
copy /Y ai_earnings_today.html "C:\Users\Tyler_AI\Desktop\14 days earning screener.html" >nul

REM Git commit and push (triggers Nixpacks rebuild on Railway)
"C:\Program Files\Git\cmd\git.exe" add ai_earnings_today.html scanner.html scanner_data.json pick_tracker.json
"C:\Program Files\Git\cmd\git.exe" commit -m "Daily scan update"
"C:\Program Files\Git\cmd\git.exe" push origin master

echo [DONE] Scanner complete, pushed to Railway
