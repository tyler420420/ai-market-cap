# Runs the daily scan under Task Scheduler, capturing EVERYTHING.
#
# WHY THIS EXISTS
# ---------------
# Both AIScannerDaily (13:00) and AIScannerDaily1 (06:31) run this same script
# and both were reporting LastTaskResult = 1, having written ZERO lines to
# daily_scan.log. The only successful recent run was manual, at 23:37 on the
# 22nd. So the unattended path fails silently: exit code 1, no evidence, and
# nothing notices because the site keeps serving yesterday's HTML until someone
# runs it by hand.
#
# Two fixes live here rather than in daily_scan.ps1, so the scan script itself
# stays the single writer it is documented to be:
#
#   1. Duplicate task removed. daily_scan.ps1's own header says three tasks
#      used to race each other and "single task now; this script is the ONLY
#      writer" - yet two were still registered, due at 06:31 and 13:00.
#      AIScannerDaily (13:00) is disabled; AIScannerDaily1 (06:31) is the one
#      that survives, because it is the one the alert follow-up checks.
#
#   2. All output captured. Whatever the script writes to the console, plus
#      anything on stderr, lands in scheduled_run.log with a timestamped
#      header. Task Scheduler's own history rotates away; this does not.
$ErrorActionPreference = 'Continue'

$repo = 'C:\Users\Tyler_AI\ai-market-cap'
$scan = Join-Path $repo 'daily_scan.ps1'
$log  = Join-Path $repo 'scheduled_run.log'

function Stamp { (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') }

"===== [$(Stamp)] scheduled run STARTED (pid $PID) =====" | Out-File -FilePath $log -Append -Encoding utf8

$before = if (Test-Path $log) { (Get-Item $log).Length } else { 0 }

try {
    $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scan 2>&1
    $code = $LASTEXITCODE
    $output | Out-File -FilePath $log -Append -Encoding utf8
    "----- [$(Stamp)] daily_scan.ps1 exited $code -----" | Out-File -FilePath $log -Append -Encoding utf8
}
catch {
    "----- [$(Stamp)] WRAPPER ERROR: $($_.Exception.Message) -----" |
        Out-File -FilePath $log -Append -Encoding utf8
    $_ | Out-String | Out-File -FilePath $log -Append -Encoding utf8
    $code = 1
}

# Trim so an unattended failure cannot fill the disk.
if ((Get-Item $log).Length -gt 2MB) {
    Get-Content $log -Tail 400 | Out-File -FilePath $log -Encoding utf8
    "----- [$(Stamp)] log rotated -----" | Out-File -FilePath $log -Append -Encoding utf8
}

"===== [$(Stamp)] scheduled run FINISHED (exit $code) =====" | Out-File -FilePath $log -Append -Encoding utf8
exit $code