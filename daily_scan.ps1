# AIScannerDaily - hardened daily scan + deploy
#
# Fixes the 10/20 outage root causes:
#   1. THREE scheduled tasks all committed/pushed the same files 30 min apart,
#      racing each other and diverging local from origin/master.
#      -> single task now; this script is the ONLY writer.
#   2. Local branch had been rewound to a pre-fix commit, so daily commits
#      stacked on stale code and never reached GitHub.
#      -> hard reset to origin/master BEFORE scanning.
#   3. "Pushed successfully" printed even when git push was rejected.
#      -> push exit code checked AND remote SHA verified against local SHA.
#   4. Concurrent runs could interleave git commands.
#      -> lock file so a second run exits immediately.
#   5. No visibility when things broke.
#      -> daily_scan.log, last 30 runs kept.

$ErrorActionPreference = 'Stop'

$repo      = 'C:\Users\Tyler_AI\ai-market-cap'
$scanner   = Join-Path $repo 'ai_earnings_scanner.py'
$python    = 'C:\Users\Tyler_AI\AppData\Local\Python\pythoncore-3.14-64\python.exe'
$git       = 'C:\Program Files\Git\cmd\git.exe'
$log       = Join-Path $repo 'daily_scan.log'
$lockFile  = Join-Path $repo '.scan.lock'
$desktop   = 'C:\Users\Tyler_AI\Desktop\14 days earning screener.html'
$siteUrl   = 'https://aismarketcap.com/'

$env:PATH = 'C:\Users\Tyler_AI\AppData\Local\Python\pythoncore-3.14-64;' +
            'C:\Users\Tyler_AI\AppData\Local\Python\pythoncore-3.14-64\Scripts;' +
            'C:\Program Files\Git\cmd;' +
            'C:\Windows\system32;C:\Windows;C:\Windows\System32\WindowsPowerShell\v1.0'

function Log($msg) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg"
    Write-Host $line
    Add-Content -Path $log -Value $line
}

# ---- rotate log so it never grows unbounded -------------------------------
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 2MB)) {
    Move-Item -Force $log "$log.1"
}

# ---- single-writer lock ------------------------------------------------------
# LIVENESS is the primary signal, staleness only a backstop.
#
# Previously the only test was "is the lock younger than 30 minutes", so an
# interrupted scan left .scan.lock behind and every scheduled run skipped until
# that timeout expired. One crashed scan therefore cost a 30-minute blind
# window. Now: if the lock exists but no scan process is actually alive, the
# lock is dead and is cleared immediately, so an interrupted scan costs exactly
# one run instead of half an hour.
$me = $PID
$alive = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessId -ne $me -and
                   $_.CommandLine -match 'daily_scan\.ps1|ai_earnings_scanner\.py' })

# Only the run that CREATED the lock may remove it. Without this, a run that
# skips because someone else is scanning would fall into `finally` and delete
# the live lock out from under the process that owns it.
$ownsLock = $false

try {
    if (Test-Path $lockFile) {
        if ($alive.Count -gt 0) {
            Log "[LOCK] a scan is genuinely running (PID $($alive.ProcessId -join ',')) - skipping this run"
            exit 0
        }
        $lockAge = (Get-Date) - (Get-Item $lockFile).CreationTime
        Log ("[LOCK] stale lock ({0} min old) but no scan process alive - clearing and continuing" -f [math]::Round($lockAge.TotalMinutes, 1))
        Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
    }
    New-Item -ItemType File -Path $lockFile -Force | Out-Null
    $ownsLock = $true
    Log "[LOCK] acquired"

    Log "===== Daily scan starting ====="
    Set-Location $repo

    # ---- 1. hard-align local to origin/master (discards divergent history) --
    & $git fetch origin --prune 2>&1 | Out-Null
    $localSha  = (& $git rev-parse HEAD).Trim()
    $remoteSha = (& $git rev-parse origin/master).Trim()
    if ($localSha -ne $remoteSha) {
        # ---- FAIL SAFE (2026-10-21) ---------------------------------------
        # The scan now runs twice daily (06:31 open, 13:00 close), so the window
        # in which an unattended 'reset --hard' silently destroys uncommitted
        # work has doubled. Only reset when no TRACKED file is modified.
        #
        # --untracked-files=no is deliberate: untracked entries are normal
        # working state for other lanes and must NEVER block a scan.
        #
        # When dirty we SKIP the reset and keep going - the scan still runs and
        # still commits/pushes. We do not abort. The push step further down
        # already fails loudly on genuine divergence via $LASTEXITCODE, so a
        # skipped reset surfaces there instead of here.
        $dirty = @(& $git -C $repo status --porcelain --untracked-files=no)
        if ($dirty.Count -gt 0) {
            Log "[GUARD] $($dirty.Count) tracked file(s) have uncommitted changes - hard reset SKIPPED"
            foreach ($l in $dirty) { Log "[GUARD]   dirty: $l" }

            # One-line marker so the ops dashboard can surface a skipped scan
            # without parsing the log. Overwritten on each skip.
            $marker = Join-Path $repo 'scan_guard_skip.txt'
            $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
            $body = @(
                "scan_guard_skip"
                "skipped_at=$stamp"
                "reason=tracked files have uncommitted changes"
                "dirty_count=$($dirty.Count)"
                "local=$localSha"
                "remote=$remoteSha"
            ) + ($dirty | ForEach-Object { "dirty=$_" })
            Set-Content -Path $marker -Value $body -Encoding UTF8
            Log "[GUARD] marker written: $marker"
        } else {
            # ---- PRESERVE BEFORE DISCARDING (2026-10-21) --------------------
            # The dirty-tree guard above protects UNCOMMITTED work only. A local
            # COMMIT ahead of origin is still destroyed by reset --hard, and that
            # actually happened during testing: a fix of mine was eaten by the
            # reset because I had committed it. So preserve those commits on a
            # dated branch first, every time, before anything is thrown away.
            #
            # Count BEFORE the reset. After it these commits are unreachable and
            # 'origin/master..HEAD' always returns nothing - which is why the
            # earlier "Discarded divergent commits" line never printed.
            $ahead = @(& $git -C $repo log --oneline 'origin/master..HEAD' 2>$null)
            if ($ahead.Count -gt 0) {
                $stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'
                $branch = "auto-save/$stamp"
                & $git -C $repo branch $branch 2>&1 | Out-Null
                Log "[GUARD] $($ahead.Count) local commit(s) PRESERVED on branch: $branch"
                foreach ($c in $ahead) { Log "[GUARD]   preserved: $c" }
                Log "[GUARD] recover with: git reset --hard $branch"

                # Keep only the N most recent so these do not pile up forever.
                # Sorted by refname descending: the branch name is yyyyMMdd-HHmmss,
                # so lexicographic order IS chronological order.
                $keep = 10
                $autoBranches = @(& $git -C $repo for-each-ref --sort=-refname --format='%(refname:short)' 'refs/heads/auto-save/*' 2>$null)
                if ($autoBranches.Count -gt $keep) {
                    foreach ($old in $autoBranches[$keep..($autoBranches.Count - 1)]) {
                        & $git -C $repo branch -D $old 2>&1 | Out-Null
                        Log "[GUARD] pruned old auto-save branch: $old"
                    }
                }
            }

            Log "[GIT] Local $localSha != origin $remoteSha - hard reset to origin/master"
            # EAP=Continue: git emits stderr chatter (line-ending warnings) that
            # would otherwise abort this script under ErrorActionPreference=Stop.
            $prevEap0 = $ErrorActionPreference
            $ErrorActionPreference = 'Continue'
            try {
                $null = & $git reset --hard origin/master 2>&1
            } finally {
                $ErrorActionPreference = $prevEap0
            }
            if ($ahead.Count -gt 0) {
                Log "[GIT] Reset discarded $($ahead.Count) commit(s) - recoverable from $branch"
            }
        }
    } else {
        Log "[GIT] Local already in sync with origin/master"
    }

    # ---- 2. run scanner ----------------------------------------------------
    # NOTE: deliberately NOT passing --local.
    # --local rewrites asset paths to file:///C:/... which browsers refuse to
    # load in production. The same HTML is committed and deployed, so --local
    # leaked a broken favicon path to every live visitor.
    Log "[SCAN] Running scanner (--no-finviz)..."

    # CRITICAL: drop to 'Continue' around the scanner call.
    # With $ErrorActionPreference='Stop', ANY line the scanner writes to stderr
    # becomes a terminating PowerShell error and kills this script - even
    # though the scanner itself succeeds. yfinance prints routine notices like
    # 'No fundamentals data found for symbol: KLA' to stderr for any ticker
    # Yahoo has no fundamentals for. That is normal, not a failure.
    #
    # This silently aborted the 7 AM scan on 2026-10-20 with:
    #   [FATAL] HTTP Error 404 ... No fundamentals data found for symbol: KLA
    # Real success is determined by $LASTEXITCODE, not by stderr noise.
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $scanOut = & $python $scanner --no-finviz 2>&1
    } finally {
        $ErrorActionPreference = $prevEap
    }
    $scanCode = $LASTEXITCODE
    # drop stderr noise from the tail so real errors stay visible
    $scanTail = ($scanOut |
        Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] } |
        Select-Object -Last 6) -join ' | '
    if ($scanCode -ne 0) {
        Log "[SCAN] FAILED exit=$scanCode :: $scanTail"
        exit 1
    }
    Log "[SCAN] OK :: $scanTail"

    # ---- 3. sanity-check the generated HTML -------------------------------
    $html = Join-Path $repo 'ai_earnings_today.html'
    if (-not (Test-Path $html)) { Log "[CHECK] FAIL - ai_earnings_today.html missing"; exit 1 }
    $size = (Get-Item $html).Length
    $content = Get-Content $html -Raw -Encoding UTF8
    if ($size -lt 150000)  { Log "[CHECK] FAIL - html too small ($size bytes)"; exit 1 }
    if ($content -notmatch 'var rowsData=') { Log "[CHECK] FAIL - rowsData missing"; exit 1 }
    $rowCount = ([regex]::Matches($content, '"ticker"\s*:')).Count
    if ($rowCount -lt 20)  { Log "[CHECK] FAIL - only $rowCount rows"; exit 1 }
    Log "[CHECK] OK - $size bytes, $rowCount stocks, data-labels=$(([regex]::Matches($content,'data-label=')).Count)"

    # ---- 3b. regression guard on the GENERATED artifact -----------------
    # The source can be correct while the shipped HTML is stale (that is how
    # 'Overall Score' + empty sentiment cells shipped twice). Assert on the
    # file users actually receive.
    $verifier = Join-Path $repo 'verify_output.py'
    if (Test-Path $verifier) {
        $vOut = & $python $verifier 2>&1
        $vCode = $LASTEXITCODE
        foreach ($line in $vOut) { Log "[VERIFY] $line" }
        if ($vCode -ne 0) {
            Log "[VERIFY] REGRESSION DETECTED - refusing to deploy broken HTML"
            exit 1
        }
    } else {
        Log "[VERIFY] WARN - verify_output.py missing, skipping regression guard"
    }

    # ---- 4. desktop copy ---------------------------------------------------
    try {
        Copy-Item $html $desktop -Force
        Log "[DESKTOP] Copied"
    } catch { Log "[DESKTOP] WARN - $_" }

    # ---- 5. commit + push (verified) --------------------------------------
    # All git calls run under EAP=Continue for the same reason as the scanner:
    # git writes harmless chatter to stderr ("LF will be replaced by CRLF",
    # "warning: LF will be replaced..."), and with Stop that is fatal.
    $prevEap2 = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $git add ai_earnings_today.html scanner_data.json ai_earnings_scanner.py `
                    ipo_etf_data.json pick_tracker.json daily_scan.ps1 2>&1 | Out-Null

        $staged = $false
        & $git diff --cached --quiet
        if ($LASTEXITCODE -ne 0) { $staged = $true }

        if (-not $staged) {
            Log "[GIT] No data changes to commit"
        } else {
            $null = & $git commit -m "Daily scan - $(Get-Date -Format 'yyyy-MM-dd HH:mm') PT" 2>&1
            $sha = (& $git rev-parse --short HEAD).Trim()
            Log "[GIT] Committed $sha"
        }

        $pushed = $false
        for ($try = 1; $try -le 3; $try++) {
            $pushOut = & $git push origin master 2>&1
            if ($LASTEXITCODE -eq 0) { $pushed = $true; Log "[GIT] Push OK (attempt $try)"; break }
            Log "[GIT] Push FAILED (attempt $try): $(($pushOut | Select-Object -Last 2) -join ' ')"
            Start-Sleep -Seconds 10
            $null = & $git pull --rebase --autostash origin master 2>&1
        }

        # ---- 6. VERIFY the push actually landed ---------------------------
        $null = & $git fetch origin --prune 2>&1
        $finalLocal  = (& $git rev-parse HEAD).Trim()
        $finalRemote = (& $git rev-parse origin/master).Trim()
    } finally {
        $ErrorActionPreference = $prevEap2
    }

    if ($finalLocal -eq $finalRemote) {
        Log "[VERIFY] OK - local == origin/master ($($finalLocal.Substring(0,7)))"
    } else {
        Log "[VERIFY] FAIL - local $finalLocal != remote $finalRemote. DATA NOT DEPLOYED."
        exit 1
    }

    # ---- 7. site health check --------------------------------------------
    # Confirm the deployment actually serves healthy content, and that the
    # feature checks still hold over HTTP (not just in the local file).
    try {
        $resp = Invoke-WebRequest -Uri $siteUrl -UseBasicParsing -TimeoutSec 25
        Log "[SITE] HTTP $($resp.StatusCode), $($resp.Content.Length) bytes"
        if ($resp.StatusCode -ne 200) { Log "[SITE] WARN - non-200" }
    } catch {
        Log "[SITE] ERROR - $($_.Exception.Message)"
        Log "[SITE] NOTE: if this is '404 / x-railway-fallback', the Railway service"
        Log "[SITE]       is down and needs a manual Restart in the Railway dashboard."
    }

    # Live feature audit - catches "source is fine but the deploy is stale"
    $auditor = Join-Path $repo 'audit_live.py'
    if (Test-Path $auditor) {
        $aOut = & $python $auditor 2>&1
        $aCode = $LASTEXITCODE
        foreach ($line in ($aOut | Select-Object -Last 6)) { Log "[AUDIT] $line" }
        if ($aCode -ne 0) {
            Log "[AUDIT] FAILURES DETECTED on the live site - see output above"
        } else {
            Log "[AUDIT] Live site clean"
        }
    }

    Log "===== Daily scan complete (pushed=$pushed) ====="
}
catch {
    Log "[FATAL] $_"
    exit 1
}
finally {
    if ($ownsLock -and (Test-Path $lockFile)) {
        Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
        Log "[LOCK] released on exit"
    }
}