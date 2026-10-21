# AISiteIndex - daily stock-page generation + search-engine submission
#
# Runs at 08:15 PT, after the 07:00 scanner and the 07:00 article generator.
#
# Order matters. New URLs must be LIVE before they are submitted, otherwise
# Google/Bing crawl a 404 and the pages never get indexed. So this script:
#   1. generate/refresh stock pages        (idempotent - 24h freshness skip)
#   2. reconcile blog/index.json           (picks up articles written since)
#   3. commit + push                       (never discards local work)
#   4. WAIT for Railway to actually serve the new pages
#   5. only then ping Google + Bing sitemaps
#
# Failure policy: indexing never blocks anything. Every stage is wrapped, a
# platform being down is logged and skipped, and the script always exits 0
# unless it could not even start.

$ErrorActionPreference = 'Stop'

$repo    = 'C:\Users\Tyler_AI\ai-market-cap'
$python  = 'C:\Users\Tyler_AI\AppData\Local\Python\pythoncore-3.14-64\python.exe'
$git     = 'C:\Program Files\Git\cmd\git.exe'
$site    = 'https://aismarketcap.com'
$log     = Join-Path $repo 'indexing.log'
$lock    = Join-Path $repo '.index.lock'
$sitemap = "$site/sitemap.xml"

function Log($msg) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg"
    Write-Host $line
    Add-Content -Path $log -Value $line -Encoding UTF8
}

# Rotate the log so it cannot grow without bound.
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 1MB)) {
    Move-Item -Force $log "$log.1"
}

# Single-writer lock: the 7 AM scanner and the 5-min watchdog share this box.
if (Test-Path $lock) {
    $age = (Get-Date) - (Get-Item $lock).CreationTime
    if ($age.TotalMinutes -lt 30) {
        Log "[SKIP] Another job holds the lock ($([int]$age.TotalMinutes) min)"
        exit 0
    }
    Log "[WARN] Removing stale lock ($([int]$age.TotalMinutes) min old)"
}
New-Item -ItemType File -Path $lock -Force | Out-Null

# Native commands must never run under ErrorActionPreference='Stop' - stderr
# chatter from git/python/yfinance would abort the script. Success is decided
# by $LASTEXITCODE only. (This exact bug killed the 07:00 scan on 2026-10-20.)
$ErrorActionPreference = 'Continue'
$pushFailed = $false
$pagesChanged = $false

try {
    Log "===== Daily indexing starting ====="
    Set-Location $repo

    # ---------- 1. stock pages ------------------------------------------
    Log "[1/5] Generating/refreshing stock pages..."
    $genOut = & $python generate_stock_pages.py 2>&1
    $genCode = $LASTEXITCODE
    $genClean = ($genOut | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] })
    $summary = ($genClean | Where-Object { $_ -match '^Done:' } | Select-Object -Last 1)
    if ($summary) { Log "[1/5] $summary" }
    else { Log "[1/5] generator output: $(($genClean | Select-Object -Last 2) -join ' | ')" }
    if ($genCode -ne 0) { Log "[1/5] WARN - generator exit $genCode, continuing" }

    $pagesChanged = ((& $git status --porcelain -- stock_pages 2>$null) | Measure-Object).Count -gt 0
    Log "[1/5] stock_pages changed: $pagesChanged"

    # ---------- 2. reconcile the blog index ------------------------------
    # blog/index.json drives sitemap.xml. An article HTML written without an
    # index entry is invisible to search engines. sync_blog_index.py adds the
    # orphans, never re-indexes a retired (purged) slug, and never indexes the
    # scanner output. It is idempotent and safe to run every day.
    Log "[2/5] Reconciling blog/index.json..."
    $rcOut = & $python sync_blog_index.py 2>&1
    $rcCode = $LASTEXITCODE
    $rcLine = ($rcOut | Where-Object { $_ -match '^SYNC:' } | Select-Object -Last 1)
    if ($rcLine) { Log "[2/5] $rcLine" }
    else { Log "[2/5] WARN - reconciler gave no summary (exit $rcCode), continuing" }

    # ---------- 3. commit + push -----------------------------------------
    Log "[3/5] Committing + pushing..."
    $null = & $git fetch origin --prune 2>&1
    $null = & $git add stock_pages blog 2>&1

    & $git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Log "[3/5] Nothing new to publish (idempotent no-op)"
    } else {
        $null = & $git commit -m "Index update - $(Get-Date -Format 'yyyy-MM-dd HH:mm') PT" 2>&1
        $null = & $git push origin master 2>&1
        if ($LASTEXITCODE -eq 0) {
            Log "[3/5] Pushed $((& $git rev-parse --short HEAD).Trim())"
        } else {
            $pushFailed = $true
            Log "[3/5] WARN - push failed, skipping ping (pages are not live)"
        }
    }

    # ---------- 4. wait for Railway to serve the new pages ----------------
    if ($pushFailed) {
        Log "[4/5] Skipped - nothing pushed"
    } else {
        Log "[4/5] Waiting for Railway to serve the deploy..."
        $deadline = (Get-Date).AddMinutes(8)
        $live = $false
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Seconds 20
            try {
                $r = Invoke-WebRequest -Uri "$sitemap" -UseBasicParsing -TimeoutSec 20
                if ($r.StatusCode -eq 200) { $live = $true; break }
            } catch { }
        }
        if ($live) { Log "[4/5] Sitemap live - safe to submit" }
        else { Log "[4/5] WARN - sitemap not responding; submitting anyway (non-fatal)" }
    }

    # ---------- 5. submit to search engines -------------------------------
    # The old anonymous ping endpoints are DEAD:
    #     google.com/ping -> 404 "Sitemaps ping is deprecated" (retired 2023)
    #     bing.com/ping   -> 410 Gone
    # so generate_stock_pages.py --ping could never have worked, even if that
    # leap-day-only cron had ever fired.
    #
    # IndexNow is the supported replacement: free, no API key, no OAuth,
    # instant notification to Bing + partners. Google has no public endpoint;
    # it discovers the sitemap through robots.txt, which this site already
    # serves, and through Search Console if an account is connected.
    #
    # Indexing is advisory. Any failure is logged and the run still succeeds.
    Log "[5/5] Submitting changed URLs via IndexNow..."
    $ixOut = & $python indexnow_submit.py 2>&1
    $ixCode = $LASTEXITCODE
    foreach ($line in ($ixOut | Where-Object { $_ -match '^INDEXNOW' })) { Log "[5/5] $line" }
    if ($ixCode -ne 0) { Log "[5/5] WARN - indexnow exit $ixCode, continuing" }

    Log "[5/5] robots.txt sitemap declaration check..."
    try {
        $rb = Invoke-WebRequest -Uri "$site/robots.txt" -UseBasicParsing -TimeoutSec 20
        if ($rb.Content -match 'Sitemap:\s*https://aismarketcap\.com/sitemap\.xml') {
            Log "[5/5] robots.txt declares the sitemap - Google discovery path OK"
        } else {
            Log "[5/5] WARN - robots.txt does not declare $sitemap/sitemap.xml"
        }
    } catch {
        Log "[5/5] WARN - could not read robots.txt: $($_.Exception.Message)"
    }

    Log "===== Daily indexing complete ====="
    exit 0
}
catch {
    Log "[FATAL] $_"
    exit 1
}
finally {
    if (Test-Path $lock) { Remove-Item $lock -Force -ErrorAction SilentlyContinue }
}