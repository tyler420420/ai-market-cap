# AIScannerDailyPush - PowerShell wrapper for Task Scheduler
# Fixes 0x8007007F ERROR_PROC_NOT_FOUND by setting PATH explicitly
$ErrorActionPreference = 'Stop'
$projectDir = 'C:\Users\Tyler_AI\ai-market-cap'
$pythonExe = 'C:\Users\Tyler_AI\AppData\Local\Python\pythoncore-3.14-64\python.exe'
$gitExe = 'C:\Program Files\Git\cmd\git.exe'
$env:PATH = 'C:\Users\Tyler_AI\AppData\Local\Python\pythoncore-3.14-64;' +
            'C:\Users\Tyler_AI\AppData\Local\Python\pythoncore-3.14-64\Scripts;' +
            'C:\Program Files\Git\cmd;' +
            'C:\Windows\system32;' +
            'C:\Windows;' +
            'C:\Windows\System32\WindowsPowerShell\v1.0'

Set-Location $projectDir

Write-Host "[AIScanner] Starting daily scan..."

# Run scanner
$scanResult = & $pythonExe ai_earnings_scanner.py --no-finviz 2>&1
Write-Host $scanResult
if ($LASTEXITCODE -ne 0) {
    Write-Host "[AIScanner] ERROR - scanner failed with exit code $LASTEXITCODE"
    exit 1
}

# Copy fresh output to Desktop shortcut
Copy-Item -Force ai_earnings_today.html 'C:\Users\Tyler_AI\Desktop\14 days earning screener.html'

# Git commit and push (triggers Nixpacks rebuild on Railway)
& $gitExe add ai_earnings_today.html scanner_data.json pick_tracker.json
& $gitExe commit -m "Daily scan - $(Get-Date -Format 'yyyy-MM-dd hh:mm tt') PT"
& $gitExe push origin master

Write-Host "[AIScanner] Done - pushed to Railway"
