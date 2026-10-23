# Runs the on-demand scan poller continuously so a subscriber clicking "Scan"
# gets a real scan within about a minute.
#
# Tyler 2026-10-22: "point the scan to my local machine, that is best solution."
# The scanner cannot run in the Railway container (it OOM'd the container into a
# restart loop that 404'd every route). It runs fine here, where daily_scan.ps1
# already scans, commits and pushes so Railway redeploys the fresh page.
#
# This task keeps scan_poller.py alive. It is idempotent: if the poller is
# already running it does nothing, so a duplicate trigger cannot start a second
# poller and cause duplicate scans.

$ErrorActionPreference = 'Stop'
$here = 'C:\Users\Tyler_AI\ai-market-cap'
$poller = Join-Path $here 'scan_poller.py'
$python = 'C:\Users\Tyler_AI\AppData\Local\Python\pythoncore-3.14-64\python.exe'

if (-not (Test-Path $poller)) { Write-Host "scan_poller.py not found at $poller"; exit 1 }

# Already running? Do nothing.
$running = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'scan_poller\.py' }
if ($running) {
    Write-Host "scan_poller already running (PID $($running.ProcessId -join ','))"
    exit 0
}

Write-Host "starting scan_poller..."
Start-Process -FilePath $python -ArgumentList $poller -WindowStyle Hidden -WorkingDirectory $here
Start-Sleep -Seconds 4
$now = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'scan_poller\.py' }
if ($now) {
    Write-Host "scan_poller started (PID $($now.ProcessId))"
    Get-Content (Join-Path $here 'scan_poller.log') -Tail 3 -ErrorAction SilentlyContinue
} else {
    Write-Host "scan_poller FAILED to start - check scan_poller.log"
    exit 1
}