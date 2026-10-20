# AISiteWatch - uptime monitor + auto-recovery for aismarketcap.com
#
# Runs every 5 minutes. Checks the live site, logs status, and attempts
# recovery when it goes down.
#
# Recovery ladder (tries each in order, stops as soon as the site returns):
#   1. Restart the Railway service via API   (needs RAILWAY_TOKEN)
#   2. Trigger a Railway redeploy by pushing an empty commit
#   3. Escalate - write an alert file + log loudly
#
# This is what keeps the site up: detection within 5 min, auto-recovery
# without you having to notice.

$ErrorActionPreference = 'Stop'

$repo     = 'C:\Users\Tyler_AI\ai-market-cap'
$log      = Join-Path $repo 'uptime_log.csv'
$alert    = Join-Path $repo 'SITE_DOWN_ALERT.txt'
$git      = 'C:\Program Files\Git\cmd\git.exe'
$site     = 'https://aismarketcap.com/'
$lockFile = Join-Path $repo '.watch.lock'

# Railway project/service IDs (from the dashboard URL)
$RAILWAY_PROJECT_ID = 'cc9ba7df-fa0c-4248-9c3c-deb7b9c8cbea'
$RAILWAY_SERVICE_ID = '98f3caa8-21b4-4d53-9b1c-a9fe59119ad6'
$RAILWAY_ENV_ID     = ''          # optional, Railway fills this in
$RAILWAY_TOKEN      = ''          # paste a Railway API token here for full auto-restart

$env:PATH = 'C:\Program Files\Git\cmd;C:\Windows\system32;C:\Windows;C:\Windows\System32\WindowsPowerShell\v1.0'

function Log($msg) {
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg"
}

# ---- prevent overlapping runs ------------------------------------------------
if (Test-Path $lockFile) {
    $age = (Get-Date) - (Get-Item $lockFile).CreationTime
    if ($age.TotalMinutes -lt 4) { exit 0 }
    Remove-Item $lockFile -Force
}
New-Item -ItemType File -Path $lockFile -Force | Out-Null

function Clear-DownState {
    if (Test-Path $alert) { Remove-Item $alert -Force }
}

function Write-Alert($reason, $detail) {
    $msg = @"
SITE DOWN - aismarketcap.com
Detected : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Reason   : $reason
Detail   : $detail
Action   : Check https://railway.com/project/$RAILWAY_PROJECT_ID/service/$RAILWAY_SERVICE_ID
"@
    Set-Content -Path $alert -Value $msg -Encoding UTF8
}

function Test-Site {
    try {
        $r = Invoke-WebRequest -Uri $site -UseBasicParsing -TimeoutSec 20
        if ($r.StatusCode -eq 200 -and $r.Content.Length -gt 50000) {
            return @{ Ok = $true; Code = $r.StatusCode; Len = $r.Content.Length; Note = '' }
        }
        return @{ Ok = $false; Code = $r.StatusCode; Len = $r.Content.Length
                  Note = "HTTP $($r.StatusCode) / $($r.Content.Length) bytes (suspicious body)" }
    } catch {
        $code = 'n/a'; $fb = ''
        if ($_.Exception.Response) {
            $code = [int]$_.Exception.Response.StatusCode
            $fb  = $_.Exception.Response.Headers['x-railway-fallback']
        }
        return @{ Ok = $false; Code = $code; Len = 0
                  Note = "$($_.Exception.Message) [fallback=$fb]" }
    }
}

try {
    $s = Test-Site

    # append to CSV log
    if (-not (Test-Path $log)) {
        Set-Content -Path $log -Value "timestamp,status,code,bytes,note" -Encoding UTF8
    }
    $status = if ($s.Ok) { 'UP' } else { 'DOWN' }
    Add-Content -Path $log -Value "$((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),$status,$($s.Code),$($s.Len),`"$($s.Note)`"" -Encoding UTF8

    # keep log under ~2MB
    if ((Get-Item $log).Length -gt 2MB) {
        Move-Item -Force $log "$log.1"
        Set-Content -Path $log -Value "timestamp,status,code,bytes,note" -Encoding UTF8
    }

    if ($s.Ok) {
        if (Test-Path $alert) { Log "RECOVERED - site is back up ($($s.Len) bytes). Clearing alert."; Clear-DownState }
        else { Log "UP - $($s.Code), $($s.Len) bytes" }
        exit 0
    }

    # ---------- site is DOWN ----------
    if (Test-Path $alert) {
        Log "DOWN (already alerted) - $($s.Note)"
        exit 1
    }

    Log "DOWN - $($s.Note)"
    Log "Attempting recovery..."

    # Recovery 1: Railway API restart
    $recovered = $false
    if ($RAILWAY_TOKEN) {
        try {
            $hdr = @{ 'Authorization' = "Bearer $RAILWAY_TOKEN"
                      'Content-Type'  = 'application/json' }
            $body = @{ 'serviceId' = $RAILWAY_SERVICE_ID } | ConvertTo-Json
            $apiUrl = if ($RAILWAY_ENV_ID) {
                "https://backboard.railway.com/graphql/v2/environments/$RAILWAY_ENV_ID/services/$RAILWAY_SERVICE_ID/restart"
            } else {
                "https://backboard.railway.com/graphql/v2/services/$RAILWAY_SERVICE_ID/restart"
            }
            Invoke-RestMethod -Uri $apiUrl -Method Post -Headers $hdr -Body $body -TimeoutSec 20 | Out-Null
            Log "Railway restart API called. Waiting 45s..."
            Start-Sleep -Seconds 45
            $s2 = Test-Site
            if ($s2.Ok) { $recovered = $true; Log "RECOVERED via Railway restart API" }
            else { Log "Railway restart did not help: $($s2.Note)" }
        } catch {
            Log "Railway restart API failed: $($_.Exception.Message)"
        }
    } else {
        Log "No RAILWAY_TOKEN set - skipping API restart."
    }

    # Recovery 2: nudge a Railway redeploy with an empty commit.
    #
    # SAFETY: the watchdog must NEVER mutate the working tree.
    #   Original line here was `git reset --hard origin/master`, which destroyed
    #   uncommitted edits on every down event. Replacing it with
    #   `git stash push -u` avoided the data loss but was still wrong here:
    #   this repo carries ~500 untracked artifacts (_*.py scratch scripts,
    #   ai_earnings_57day_*.html snapshots), so `stash -u` would sweep all of
    #   them into a stash and never restore them, and `git merge` could leave
    #   the repo mid-conflict on a timer the user never asked for.
    #
    # Correct behaviour: only commit when the tree is clean. If the user has
    # work in progress, refuse and report - the daily scan (lock-protected,
    # the authorised writer) owns repo surgery.
    if (-not $recovered) {
        try {
            Set-Location $repo
            $null = & $git fetch origin --prune 2>&1

            $dirty = @(& $git status --porcelain 2>$null)
            if ($dirty.Count -gt 0) {
                Log "REDEPLOY SKIPPED - working tree has $($dirty.Count) uncommitted change(s)."
                Log "  Commit or stash them yourself, then the redeploy can proceed."
                Log "  First few: $(($dirty | Select-Object -First 3 | ForEach-Object { $_.Trim() }) -join ' / ')"
            } else {
                # NOTE: do NOT pipe through Out-Null - piping resets $LASTEXITCODE.
                $null = & $git commit --allow-empty -m "Watchdog: force Railway redeploy $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>&1
                $push = & $git push origin master 2>&1
                $pushCode = $LASTEXITCODE
                if ($pushCode -eq 0) {
                    Log "Redeploy triggered (empty commit pushed). Waiting 90s..."
                    Start-Sleep -Seconds 90
                    $s3 = Test-Site
                    if ($s3.Ok) { $recovered = $true; Log "RECOVERED via redeploy" }
                    else { Log "Redeploy did not help yet: $($s3.Note)" }
                } else {
                    Log "Redeploy push failed (exit $pushCode): $(($push | Select-Object -Last 2) -join ' / ')"
                }
            }
        } catch {
            Log "Redeploy attempt failed: $($_.Exception.Message)"
        }
    }

    if ($recovered) { Clear-DownState; exit 0 }

    # ---------- could not fix it ----------
    Write-Alert $s.Code $s.Note
    Log "COULD NOT AUTO-RECOVER. Alert written to $alert"
    exit 1
}
catch {
    Log "Monitor error: $_"
    exit 2
}
finally {
    if (Test-Path $lockFile) { Remove-Item $lockFile -Force -ErrorAction SilentlyContinue }
}