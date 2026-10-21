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

# NOTE: a previous version had `if (-not $IsWindows -and $false) { }` here with a
# comment about git needing the executable bit. That condition can never be
# true, so it did nothing while appearing to handle the case. On Windows the exec
# bit is not used by git-for-windows, so no chmod is needed; the check that
# actually matters is whether the hook file landed, which is verified below.

if (-not (Test-Path $dst)) {
    Write-Host "ERROR: hook did not land at $dst" -ForegroundColor Red
    exit 1
}

# Confirm the installed copy is byte-identical to the tracked source. A hook
# that has drifted from .githooks/pre-commit is a guard that no longer guards.
$srcHash = (Get-FileHash $src -Algorithm SHA256).Hash
$dstHash = (Get-FileHash $dst -Algorithm SHA256).Hash
if ($srcHash -ne $dstHash) {
    Write-Host "ERROR: installed hook does not match .githooks\pre-commit" -ForegroundColor Red
    exit 1
}

Write-Host "Installed pre-commit gate -> .git\hooks\pre-commit"
Write-Host ("SHA256 verified: " + $dstHash.Substring(0, 16))
Write-Host ""
Write-Host "This now BLOCKS any commit that stages a broken ai_earnings_today.html."
Write-Host "Emergency bypass: SKIP_GUARD=1 git commit ..."