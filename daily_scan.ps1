$ErrorActionPreference = "Stop"
$repo = "C:\Users\Tyler_AI\ai-market-cap"
$scanner = "$repo\ai_earnings_scanner.py"
$python = "C:\Users\Tyler_AI\AppData\Local\Microsoft\WindowsApps\python.exe"
$desktop_html = "C:\Users\Tyler_AI\Desktop\14 days earning screener.html"
$desktop_test = "C:\Users\Tyler_AI\Desktop\test_scanner.html"

Write-Host "[Daily Scan] Starting at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') PT"

# Run scanner
Write-Host "[Daily Scan] Running scanner..."
& $python $scanner --no-finviz --local

# Copy fresh HTML to desktop and repo
Write-Host "[Daily Scan] Copying HTML..."
Copy-Item "$repo\ai_earnings_today.html" $desktop_html -Force
Copy-Item "$repo\ai_earnings_today.html" $desktop_test -Force

# Git commit & push
Set-Location $repo
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
git add ai_earnings_today.html scanner_data.json ai_earnings_scanner.py
$status = git status --short
if ($status) {
    git commit -m "Daily scan - $timestamp PT"
    git push
    Write-Host "[Daily Scan] Pushed successfully at $timestamp PT"
} else {
    Write-Host "[Daily Scan] No changes to commit"
}

Write-Host "[Daily Scan] Done at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') PT"
