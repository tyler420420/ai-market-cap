$ErrorActionPreference = "Stop"
$repo = "C:\Users_Tyler_AI\ai-market-cap"
$scanner = "$repo\ai_earnings_scanner.py"
$python = "C:\Users_Tyler_AI\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$desktop_html = "C:\Users_Tyler_AI\Desktop\14 days earning screener.html"
$log = "$repo\daily_scan.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"

function Log($msg) {
    $line = "[$timestamp] $msg"
    Write-Host $line
    Add-Content -Path $log -Value $line
}

Log "[Daily Scan] Starting"

Set-Location $repo

# Pull latest so we don't diverge from remote
try {
    git pull --rebase --autostash 2>&1 | Out-Null
    Log "[Daily Scan] Git pull --rebase OK"
} catch {
    Log "[Daily Scan] Git pull failed: $_"
}

# Run scanner
Log "[Daily Scan] Running scanner..."
& $python $scanner --no-finviz --local 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Log "[Daily Scan] Scanner FAILED (exit $LASTEXITCODE)"
    exit 1
}
Log "[Daily Scan] Scanner done"

# Copy fresh HTML to desktop
try {
    Copy-Item "$repo\ai_earnings_today.html" $desktop_html -Force
    Log "[Daily Scan] Copied to desktop"
} catch {
    Log "[Daily Scan] Desktop copy failed: $_"
}

# Git commit
git add ai_earnings_today.html scanner_data.json ai_earnings_scanner.py ipo_etf_data.json 2>&1 | Out-Null
$status = git status --short
if ($status) {
    git commit -m "Daily scan - $timestamp PT" 2>&1 | Out-Null
    Log "[Daily Scan] Committed"

    # Push with rebase
    $pushOut = git push 2>&1
    if ($LASTEXITCODE -eq 0) {
        Log "[Daily Scan] Pushed OK"
    } else {
        Log "[Daily Scan] Push FAILED: $pushOut"
        # Try pull+repush
        try {
            git pull --rebase --autostash 2>&1 | Out-Null
            $pushOut2 = git push 2>&1
            if ($LASTEXITCODE -eq 0) {
                Log "[Daily Scan] Pushed OK after rebase"
            } else {
                Log "[Daily Scan] Push STILL FAILED: $pushOut2"
            }
        } catch {
            Log "[Daily Scan] Rebase+push failed: $_"
        }
    }
} else {
    Log "[Daily Scan] No changes to commit"
}

Log "[Daily Scan] Done"
