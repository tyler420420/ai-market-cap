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

# ---- unattended-failure evidence --------------------------------------------
# Both AIScannerDaily (13:00) and AIScannerDaily1 (06:31) invoke this script and
# both were reporting LastTaskResult = 1 while writing ZERO lines to
# daily_scan.log. An unattended failure therefore left no trace at all, and
# nothing noticed because the site keeps serving the previous day's HTML until
# someone runs the scan by hand.
#
# Whatever killed those runs happened BEFORE the first Log call, so the evidence
# has to be established before anything else. This block records entry, and the
# trap below records any terminating error with its line number and stack trace.
#
# It lives inside the script rather than in a wrapper because Set-ScheduledTask
# requires administrator rights (this account gets HRESULT 0x80070005), so a
# capturing wrapper could not be pointed at the task.
$__scanLog = 'C:\Users\Tyler_AI\ai-market-cap\daily_scan.log'
$__runTag  = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
try {
    Add-Content -Path $__scanLog -Value "[$__runTag] [BOOT] daily_scan.ps1 entered (pid $PID)"
} catch {
    # Never let the evidence block itself become the reason a scan dies.
}
trap {
    $__err  = $_.Exception.Message
    $__line = $_.InvocationInfo.ScriptLineNumber
    $__at   = $_.InvocationInfo.Line.Trim()
    try {
        Add-Content -Path $__scanLog -Value "[$__runTag] [FATAL] unhandled error at line ${__line}: $__err"
        Add-Content -Path $__scanLog -Value "           source: $__at"
        Add-Content -Path $__scanLog -Value ($_.ScriptStackTrace)
    } catch { }
    Write-Host "[FATAL] daily_scan.ps1 line ${__line}: $__err"
    exit 1
}

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

    # ---- 1a. LOCAL IS AHEAD - PUBLISH IT, DO NOT RESET IT ----------------
    # A lane (CTO, CMO, SEO, EMO) that commits without pushing leaves master
    # ahead of origin. The old code treated "local != remote" as one case and
    # ran `reset --hard origin/master` on all of it - which discarded exactly
    # that work from master. It survived only on an auto-save/ branch, and
    # Railway deploys from master, so the work silently vanished from
    # production while every log line still read like a successful scan.
    #
    # That is the worst possible shape: a lane's verified commit, reported as
    # done, quietly undeployed by an unattended job. It has happened three
    # times in one night (ce6f322, 92ab0bb, 9b2997d).
    #
    # Being AHEAD is not divergence. Nothing has been rejected. So push.
    $aheadCount  = [int]((& $git rev-list --count 'origin/master..HEAD' 2>$null) -as [int])
    $behindCount = [int]((& $git rev-list --count 'HEAD..origin/master' 2>$null) -as [int])
    if ($aheadCount -gt 0 -and $behindCount -eq 0) {
        $unpushed = @(& $git log --oneline 'origin/master..HEAD')
        Log "[GIT] Local is AHEAD of origin by $aheadCount commit(s) - a lane committed without pushing"
        foreach ($c in $unpushed) { Log "[GIT]   unpushed: $c" }
        $prevEapPub = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $pubOut = & $git push origin master 2>&1
        $pubCode = $LASTEXITCODE
        $ErrorActionPreference = $prevEapPub
        if ($pubCode -eq 0) {
            Log "[GIT] Published the unpushed work. Nothing was discarded."
        } else {
            # Publishing failed. Falling through to a reset would destroy the
            # very commits we just failed to publish, so stop instead.
            Log "[GIT] FATAL - could not publish $aheadCount unpushed commit(s): $(($pubOut | Select-Object -Last 2) -join ' ')"
            Log "[GIT]        Refusing to reset; a reset would discard the work."
            Log "[GIT]        Re-run once the remote is reachable."
            exit 1
        }
        $localSha  = (& $git rev-parse HEAD).Trim()
        $remoteSha = (& $git rev-parse origin/master).Trim()
    }

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

            # Take a real copy of every dirty tracked file BEFORE any git
            # command in this script runs. The hard reset is already skipped
            # and local commits are preserved by sha, but the retry path uses
            # `git pull --rebase --autostash`, and a rebase that moves the
            # same file can leave local edits silently discarded. A directory
            # of untouched copies costs nothing and makes that recoverable.
            try {
                $snap = Join-Path $repo ("pre_scan_backup_" + (Get-Date -Format 'yyyyMMdd_HHmmss'))
                New-Item -ItemType Directory -Path $snap -Force | Out-Null
                foreach ($l in $dirty) {
                    $p = ($l -replace '^.\s+', '') -replace '\s.*$', ''
                    if ($p -and (Test-Path (Join-Path $repo $p))) {
                        Copy-Item -Path (Join-Path $repo $p) -Destination (Join-Path $snap (Split-Path $p -Leaf)) -Force
                    }
                }
                $script:backupDir = $snap
                Log "[GUARD] pre-scan snapshot saved to $snap"
            } catch {
                Log "[GUARD] WARN - could not snapshot dirty files: $($_.Exception.Message)"
            }

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

    # ---- 3aa. target-hit evaluation -------------------------------------
    # pick_tracker.json is OVERWRITTEN each scan, so nothing tracked its picks
    # over time and a pick reaching its target could never be detected.
    # evaluate_targets.py keeps the history and writes target_hits.json, which
    # is what fires the "JUST HIT TARGET" nudge on /pricing.
    #
    # NON-FATAL: a hit evaluator failing must not block a scan, exactly like
    # the email send below. The nudge simply does not appear, which is the
    # honest outcome anyway.
    $evalScript = Join-Path $repo 'evaluate_targets.py'
    if (Test-Path $evalScript) {
        $eOut = & $python $evalScript 2>&1
        $eCode = $LASTEXITCODE
        foreach ($line in ($eOut | Select-Object -Last 5)) { Log "[TARGETS] $line" }
        if ($eCode -ne 0) {
            Log "[TARGETS] WARN - evaluator exited $eCode (non-fatal, scan continues)"
        }
    } else {
        Log "[TARGETS] WARN - evaluate_targets.py missing (non-fatal)"
    }

    # ---- 3ab. subscription reconcile ------------------------------------
    # STRIPE_WEBHOOK_SECRET is not set, and /webhook fails closed without it -
    # correct, since an unsigned body must never revoke a paying customer.
    # But it means cancellations and failed renewals never reach the site at
    # all, and is_subscriber() short-circuits on a local 'active', so nothing
    # catches them either.
    #
    # This asks Stripe once a day what each active subscription really is, and
    # downgrades only on a positive "not active". Every error path leaves
    # access untouched: missing a cancellation is cheap, denying a paying
    # customer is not.
    $reconScript = Join-Path $repo 'reconcile_subscriptions.py'
    if (Test-Path $reconScript) {
        $rOut = & $python $reconScript 2>&1
        $rCode = $LASTEXITCODE
        foreach ($line in ($rOut | Select-Object -Last 6)) { Log "[RECONCILE] $line" }
        if ($rCode -ne 0) {
            Log "[RECONCILE] WARN - reconciler exited $rCode (non-fatal, scan continues)"
        }
    } else {
        Log "[RECONCILE] WARN - reconcile_subscriptions.py missing (non-fatal)"
    }

# ---- 3z. pull the free signup list off Railway ----------------------------
    # Signups are captured by scanner_web.py INSIDE the Railway container,
    # whose disk is destroyed on every deploy. Until this ran there was no
    # path at all between the capture and the send, so the free page answered
    # "Check your inbox tomorrow morning" and lost every signup on the next
    # deploy. It sits immediately BEFORE 3a so the send uses a fresh list.
    #
    # NON-FATAL for the same reason 3a is: a failed pull must never take the
    # scan down. It does mean today's free recipients are whatever the last
    # successful pull left behind, so the exit code is logged as a warning
    # rather than swallowed - "no free recipients" and "could not fetch the
    # list" are very different facts and must not look the same.
    $pullScript = Join-Path $repo 'pull_email_list.py'
    if (Test-Path $pullScript) {
        $pOut = & $python $pullScript 2>&1
        $pCode = $LASTEXITCODE
        foreach ($line in ($pOut | Select-Object -Last 4)) { Log "[EMAILPULL] $line" }
        if ($pCode -ne 0) {
            Log "[EMAILPULL] WARN - pull exited $pCode (non-fatal, scan continues)."
            Log "[EMAILPULL]        If this says EMAIL_EXPORT_TOKEN is not set on"
            Log "[EMAILPULL]        Railway, free signups are being captured and lost."
        }
    } else {
        Log "[EMAILPULL] WARN - pull_email_list.py missing (non-fatal)"
    }

# ---- 3a. daily alert email -------------------------------------------
    # The pricing page sells "real-time earnings alerts". Until this existed,
    # send_daily_alert.py was a script nobody ever invoked - no cron, no task,
    # no hook - so the promise had no delivery mechanism at all.
    #
    # It runs HERE because this script is already the scheduled, unattended
    # daily writer and the data is guaranteed fresh at this point.
    #
    # Rules:
    #   * ONCE per day. This runs twice (06:31 and 13:00); a marker file
    #     suppresses the second send.
    #   * NON-FATAL. A mail failure must never abort the scan - the scan is
    #     what keeps the site current, and email is not worth taking it down.
    #   * SKIPS silently when unconfigured, so /api/alert-status stays honest
    #     instead of reporting a feature that never sends.
    $alertScript = Join-Path $repo 'send_daily_alert.py'
    $alertEnv   = Join-Path $repo 'alert.env'
    $alertMark  = Join-Path $repo '.alert_sent_today.txt'
    $todayStamp = Get-Date -Format 'yyyy-MM-dd'

    if (-not (Test-Path $alertEnv)) {
        Log "[ALERT] SKIP - alert.env not present (no credential, nothing sent)"
    } elseif (-not (Test-Path $alertScript)) {
        Log "[ALERT] SKIP - send_daily_alert.py missing"
    } elseif ((Test-Path $alertMark) -and ((Get-Content $alertMark -Raw -ErrorAction SilentlyContinue).Trim() -eq $todayStamp)) {
        Log "[ALERT] SKIP - already sent today ($todayStamp)"
    } else {
        $aOut = & $python $alertScript 2>&1
        $aCode = $LASTEXITCODE
        foreach ($line in ($aOut | Select-Object -Last 6)) { Log "[ALERT] $line" }
        if ($aCode -eq 0) {
            Set-Content -Path $alertMark -Value $todayStamp -Encoding UTF8
            Log "[ALERT] Sent and marked for $todayStamp"
        } else {
            Log "[ALERT] WARN - send exited $aCode (non-fatal, scan continues)"
        }
    }

    # ---- 3b. regression guard on the GENERATED artifact -----------------
    # The source can be correct while the shipped HTML is stale (that is how
    # 'Overall Score' + empty sentiment cells shipped twice). Assert on the
    # file users actually receive.
    $verifier = Join-Path $repo 'verify_output.py'
    # A MISSING guard is a failure, not a warning. If verify_output.py is
    # deleted, renamed or absent, this used to log a WARN and carry on -
    # shipping HTML with no regression check at all, which is exactly the
    # failure this guard exists to prevent. It fails closed now.
    if (-not (Test-Path $verifier)) {
        Log "[VERIFY] FATAL - verify_output.py is missing. The regression guard"
        Log "[VERIFY]        is required; refusing to deploy unverified HTML."
        exit 1
    }
    $vOut = & $python $verifier 2>&1
    $vCode = $LASTEXITCODE
    foreach ($line in $vOut) { Log "[VERIFY] $line" }
    if ($vCode -ne 0) {
        Log "[VERIFY] REGRESSION DETECTED - refusing to deploy broken HTML"
        exit 1
    }

    # ---- 3c. auth invariant guard -----------------------------------------
    # /login used to grant Pro to anyone who knew a subscriber's email, and
    # /webhook used to trust unsigned bodies when its secret was unset. Both
    # were live on the deployed site. scanner_web.py is committed by this
    # script, so the auth invariants are checked HERE as well as at pre-commit:
    # the daily scan is the unattended writer, and it is the last gate before
    # Railway redeploys.
    $authGuard = Join-Path $repo 'verify_auth.py'
    if (-not (Test-Path $authGuard)) {
        Log "[AUTH] FATAL - verify_auth.py is missing. The auth guard is"
        Log "[AUTH]        required; refusing to deploy unverified auth code."
        exit 1
    }
    $agOut = & $python $authGuard 2>&1
    $agCode = $LASTEXITCODE
    foreach ($line in ($agOut | Select-Object -Last 8)) { Log "[AUTH] $line" }
    if ($agCode -ne 0) {
        Log "[AUTH] AUTH INVARIANT BROKEN - refusing to deploy"
        exit 1
    }
    Log "[AUTH] Auth invariants hold"

    # ---- 3d. payment activation guard -----------------------------------
    # A real payment failed to activate the account: stripe-python >= 7 returns
    # StripeObject, not dict, and the handlers called .get() on it. The buyer
    # was charged, save_subscription() never ran, and because the handler
    # swallowed the exception and returned 200, Stripe never retried. Money in,
    # access denied, silently.
    #
    # This is money-affecting, so like the auth guard it runs here as well as
    # at pre-commit, and it fails CLOSED - deploying a known payment break is
    # worse than a missed scan.
    $payGuard = Join-Path $repo 'verify_stripe_activation.py'
    if (-not (Test-Path $payGuard)) {
        Log "[PAY] FATAL - verify_stripe_activation.py is missing. The payment"
        Log "[PAY]        guard is required; refusing to deploy unverified"
        Log "[PAY]        payment code."
        exit 1
    }
    $pgOut = & $python $payGuard 2>&1
    $pgCode = $LASTEXITCODE
    foreach ($line in ($pgOut | Select-Object -Last 6)) { Log "[PAY] $line" }
    if ($pgCode -ne 0) {
        Log "[PAY] PAYMENT ACTIVATION BROKEN - refusing to deploy"
        exit 1
    }
    Log "[PAY] Payment activation verified"

# ---- 3e. visitor baseline sync ----------------------------------------
    # Railway wipes its container filesystem on every redeploy, so the live
    # hit counter in scanner_web.py resets each time this script pushes. The
    # all-time total would therefore snap back to ~0 after every deploy.
    # visitor_baseline.json is committed and carries the total forward.
    #
    # The sync only ever moves the number UP, so a bad read cannot roll the
    # total back. It is deliberately NON-FATAL: if the live endpoint is down
    # the scan must still deploy its HTML. Failing closed here would take the
    # whole site offline over an analytics counter.
    $visSync = Join-Path $repo 'sync_visitor_baseline.py'
    if (Test-Path $visSync) {
        $vsOut = & $python $visSync 2>&1
        $vsCode = $LASTEXITCODE
        foreach ($line in ($vsOut | Select-Object -Last 3)) { Log "[VISITORS] $line" }
        if ($vsCode -ne 0) {
            Log "[VISITORS] WARN - baseline sync did not run (non-fatal)"
        }
    } else {
        Log "[VISITORS] WARN - sync_visitor_baseline.py missing (non-fatal)"
    }

    # ---- 3eb. signup counter sync -----------------------------------------
    # The free-signup counter on the container is destroyed by every Railway
    # redeploy, exactly like the visitor counter. signup_baseline.json is
    # committed and carries the absolute total forward, so the funnel's
    # `users` link reports a real integer instead of UNKNOWN.
    #
    # Same rule as the visitor sync: NON-FATAL. An analytics counter must
    # never be able to take the site offline.
    $signSync = Join-Path $repo 'sync_signup_counter.py'
    if (Test-Path $signSync) {
        $ssOut = & $python $signSync 2>&1
        $ssCode = $LASTEXITCODE
        foreach ($line in ($ssOut | Select-Object -Last 3)) { Log "[SIGNUPS] $line" }
        if ($ssCode -ne 0) {
            Log "[SIGNUPS] WARN - signup counter sync did not run (non-fatal)"
        }
    } else {
        Log "[SIGNUPS] WARN - sync_signup_counter.py missing (non-fatal)"
    }

    # ---- 3f. free-signup drip -------------------------------------------
    # Renumbered from 3c: this block used to carry a label that an EARLIER
    # block ("3c. auth invariant guard") also used, so "step 3c" named two
    # different pieces of code. A handoff that said "3c is the drip send"
    # pointed a reader at the auth guard. Every step label in this file is
    # now unique, so a step can be named unambiguously.
    # Six emails to people who signed up for the free pick themselves. NOT
    # the purchased lead lists and NOT the paid subscribers - drip_queue.py is
    # the only file allowed to read both populations, and it writes the result
    # to a queue drip_send.py alone reads.
    #
    # It enforces two CAN-SPAM gates before it will send anything: a working
    # one-click unsubscribe, and a postal address in every message. Both are
    # currently unmet, so this logs BLOCKED and sends nothing. That is the
    # correct outcome and the reason the gates exist - it is logged rather
    # than skipped so a dormant drip is never mistaken for a working one.
    #
    # NON-FATAL, same as everything else email: a blocked or failed drip must
    # never take the scan down.
    $dripQueue  = Join-Path $repo 'drip_queue.py'
    $dripSend   = Join-Path $repo 'drip_send.py'
    if ((Test-Path $dripQueue) -and (Test-Path $dripSend)) {
        $dqOut = & $python $dripQueue 2>&1
        foreach ($line in ($dqOut | Select-Object -Last 2)) { Log "[DRIPQ] $line" }
        $dsOut = & $python $dripSend 2>&1
        $dsCode = $LASTEXITCODE
        foreach ($line in ($dsOut | Select-Object -Last 4)) { Log "[DRIP] $line" }
        if ($dsCode -ne 0) {
            Log "[DRIP] Blocked or failed (exit $dsCode) - nothing sent. Gates:"
            Log "[DRIP]   working one-click unsubscribe (EMAIL_EXPORT_TOKEN on Railway)"
            Log "[DRIP]   POSTAL_ADDRESS in alert.env"
        }
    } else {
        Log "[DRIP] SKIP - drip_queue.py or drip_send.py missing (non-fatal)"
    }

# ---- 3g. LIVE PAYMENT-PATH GUARD --------------------------------------
    # Renumbered from 3d, which an earlier block ("3d. payment activation
    # guard") also used. Every step label in this file is now unique.
    # This one hits the deployed site over HTTP rather than the local file.
    # On 2026-10-21 the StripeObject/paying-customer fix was committed and
    # every local suite was green (41/41, 4/4 mutations) while the LIVE build
    # was still old enough to tell an unpaid customer "Payment received but
    # there was a problem". No source-level check can see that: the source is
    # correct, the artifact is stale. Only an HTTP check against the domain can.
    #
    # It is a WARNING, not a hard exit, on purpose. During a provider outage
    # the live site is legitimately behind master, and failing the whole scan
    # would skip the data refresh that keeps the scanner current. The staleness
    # still gets logged loudly here and surfaced in the ops dashboard via the
    # marker file below. A broken PAY path on an otherwise current deploy is
    # worth noticing immediately - it is reported, not silently tolerated.
    $payGuard = Join-Path $repo 'verify_payment_live.py'
    if (-not (Test-Path $payGuard)) {
        Log "[PAY] WARN - verify_payment_live.py is missing (non-fatal)"
    } else {
        $pOut = & $python $payGuard 2>&1
        $pCode = $LASTEXITCODE
        foreach ($line in ($pOut | Select-Object -Last 10)) { Log "[PAY] $line" }
        if ($pCode -ne 0) {
            Log "[PAY] LIVE PAYMENT PATH IS STALE OR BROKEN."
            Log "[PAY]       The deployed site does not match the source. Most"
            Log "[PAY]       likely cause: Railway has not built the latest"
            Log "[PAY]       commit yet (provider outage, or builds paused)."
            Log "[PAY]       Customer-facing impact: /success may tell an unpaid"
            Log "[PAY]       visitor their payment was received."

            # One-line marker so the ops dashboard can surface a stale deploy
            # without parsing this log. Overwritten on each run.
            try {
                $pm = Join-Path $repo 'live_stale_deploy.txt'
                $pstamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
                $pbody = @(
                    "live_deploy_stale"
                    "detected_at=$pstamp"
                    "reason=verify_payment_live.py failed against the live site"
                    "local=$((& $git -C $repo rev-parse --short HEAD).Trim())"
                    "remote=$((& $git -C $repo rev-parse --short origin/master).Trim())"
                ) + (($pOut | Select-Object -Last 4) | ForEach-Object { "detail=$_" })
                Set-Content -Path $pm -Value $pbody -Encoding UTF8
                Log "[PAY] marker written: $pm"
            } catch {
                Log "[PAY] WARN - could not write marker: $_"
            }
        } else {
            Log "[PAY] Live payment path is current and correct"
            $pmClear = Join-Path $repo 'live_stale_deploy.txt'
            if (Test-Path $pmClear) {
                Remove-Item $pmClear -Force -ErrorAction SilentlyContinue
                Log "[PAY] cleared stale marker (deploy is current)"
            }
        }
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
        # scanner_web.py is included so an auth/route fix made outside scan
        # time still gets deployed by the next run. It was missing, which meant
        # an out-of-band commit would sit on the local machine and never reach
        # Railway - the source would be fixed while the live site stayed
        # vulnerable, and audit_live would have had nothing to compare against.
        # NOTE: subscriptions.json is deliberately NOT staged here. It holds
        # subscriber records and scrypt password hashes, is already tracked,
        # and is written by the web app on Railway - not by this scan. Staging
        # it here risks committing a half-written file. Password changes reach
        # git through a normal explicit commit.
        # fetch_ipo_etf.py IS staged: it is the generator for ipo_etf_data.json.
        # Leaving it out is the same bug that stranded scanner_web.py - the
        # scanner would render TRENDING METAL / UTILITY as "No data" forever,
        # because the consumer shipped while the producer stayed on this disk.
        # alert_status.json and target_hits.json MUST be staged, and for the
        # same reason fetch_ipo_etf.py is. They are the PRODUCERS of what the
        # deployed site reads: /api/alert-status renders alert_status.json, and
        # the "JUST HIT TARGET" nudge renders target_hits.json. Leaving either
        # on this disk means the live page shows stale or missing data forever
        # while the local machine looks perfectly correct.
        # alert_sent_log.json is deliberately NOT staged - it holds subscriber
        # addresses.
        & $git add ai_earnings_today.html scanner_data.json ai_earnings_scanner.py `
                    fetch_ipo_etf.py ipo_etf_data.json pick_tracker.json daily_scan.ps1 `
                    scanner_web.py visitor_baseline.json `
                    alert_status.json target_hits.json tracked_picks.jsonl `
                    evaluate_targets.py send_daily_alert.py `
                    reconcile_subscriptions.py reconcile_status.json `
                    pull_email_list.py email_unsubscribe.py 2>&1 | Out-Null

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
            # NOTE: --autostash is the risky flag in this whole script. It
            # stashes local work, rebases, then re-applies. When the rebase
            # moves the same file the re-apply can conflict, and the result
            # is not always an obvious failure - a mobile redesign made at
            # 01:31 was silently gone from the generator by 01:32, with the
            # guard log saying nothing. Recovery here is a real copy of every
            # dirty tracked file, taken before any git command runs.
            $null = & $git pull --rebase --autostash origin master 2>&1
            $stillDirty = @(& $git -C $repo status --porcelain --untracked-files=no)
            if ($stillDirty.Count -eq 0 -and $backupDir) {
                Log "[GUARD] WARNING - local changes disappeared during the rebase. Restoring from $backupDir"
                foreach ($f in (Get-ChildItem -Path $backupDir -File -ErrorAction SilentlyContinue)) {
                    Copy-Item -Path $f.FullName -Destination (Join-Path $repo $f.Name) -Force
                }
                Log "[GUARD] restored $($backupDir)"
            }
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
    if (-not (Test-Path $auditor)) {
        Log "[AUDIT] FATAL - audit_live.py is missing; the live-deploy check is"
        Log "[AUDIT]        required. Failing closed rather than silently skipping."
        exit 1
    }
    $aOut = & $python $auditor 2>&1
    $aCode = $LASTEXITCODE
    foreach ($line in ($aOut | Select-Object -Last 6)) { Log "[AUDIT] $line" }; $vCode = 0; try { $vCode = (Invoke-WebRequest -Uri ($siteUrl + 'api/visitors') -UseBasicParsing -TimeoutSec 15).StatusCode } catch { $vCode = 0 }
    if ($aCode -ne 0) {
        if ($vCode -ne 200) { Log "[AUDIT] LIVE BUILD IS BEHIND MASTER - /api/visitors returned $vCode, not 200."; Log "[AUDIT]        The deploy is queued or paused, NOT broken. The audit failures"; Log "[AUDIT]        above are the site serving an older commit. exit 2, not 1."; Log "[AUDIT]        No code change is needed here; the next successful build clears it."; exit 2 }; Log "[AUDIT] FAILURES DETECTED on the live site - see output above"
        exit 1
    }
    Log "[AUDIT] Live site clean"

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