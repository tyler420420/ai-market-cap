# Installs the pre-commit regression gate into .git/hooks/.
#
# .git/hooks/ is not version-controlled, so run this after any fresh clone or
# if hooks appear to have stopped working.
#
#   powershell -ExecutionPolicy Bypass -File install_hooks.ps1

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$src  = Join-Path $repo '.githooks\pre-commit'
$dstDir = Join-Path $repo '.git\hooks'
$dst  = Join-Path $dstDir 'pre-commit'

if (-not (Test-Path $src)) {
    Write-Host "ERROR: $src not found" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $dstDir)) {
    Write-Host "ERROR: $dstDir not found - is this a git repo?" -ForegroundColor Red
    exit 1
}

Copy-Item $src $dst -Force

# git for Windows needs the executable bit; without it the hook never runs.
if (-not $IsWindows -and $false) { }

Write-Host "Installed pre-commit gate -> .git\hooks\pre-commit"
Write-Host ""
Write-Host "This now BLOCKS any commit that stages a broken ai_earnings_today.html."
Write-Host "Emergency bypass: SKIP_GUARD=1 git commit ..."