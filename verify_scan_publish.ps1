# Prove daily_scan.ps1 PUBLISHES unpushed lane work instead of discarding it.
#
# Permanent regression guard. Run:  powershell -File verify_scan_publish.ps1
#
# Extracts the real block from the real daily_scan.ps1 and runs it against a
#
# The defect being tested: a lane commits but does not push, master is ahead of
# origin, and the scan used to run `git reset --hard origin/master` - silently
# undeploying the lane's verified commit. Railway deploys from master, so the
# work vanished from production while every log line looked successful.
#
# This EXTRACTS the real block from the real daily_scan.ps1 and executes it
# against a throwaway repo + throwaway remote. It does not copy the logic into
# a reimplementation, because a test of a copy proves nothing about the file
# that actually ships. The live repository is never touched.

$ErrorActionPreference = 'Stop'
$git  = 'C:\Program Files\Git\cmd\git.exe'
$repo = 'C:\Users\Tyler_AI\ai-market-cap'
$root = Join-Path $env:TEMP ('scanpush_' + [guid]::NewGuid().ToString('N').Substring(0,8))
$bare = Join-Path $root 'origin.git'
$work = Join-Path $root 'work'
New-Item -ItemType Directory -Path $root -Force | Out-Null

$env:GIT_AUTHOR_NAME='lane'; $env:GIT_AUTHOR_EMAIL='lane@example.com'
$env:GIT_COMMITTER_NAME='lane'; $env:GIT_COMMITTER_EMAIL='lane@example.com'

function Sh($cwd, $cmd) {
    Push-Location $cwd
    try { $out = & $git @cmd 2>&1; return ($out | Out-String).Trim() }
    finally { Pop-Location }
}

Write-Output "=== Building a throwaway repo with one unpushed commit ==="
& $git init --bare --quiet $bare | Out-Null
& $git clone --quiet $bare $work | Out-Null
Set-Content -Path (Join-Path $work 'a.txt') -Value 'one' -NoNewline
Sh $work @('add','-A') | Out-Null
Sh $work @('commit','--quiet','-m','base') | Out-Null
Sh $work @('push','--quiet','-u','origin','master') | Out-Null

# A "lane" commits but forgets to push.
Set-Content -Path (Join-Path $work 'b.txt') -Value 'two' -NoNewline
Sh $work @('add','-A') | Out-Null
Sh $work @('commit','--quiet','-m','lane work not pushed') | Out-Null

$beforeSha = Sh $work @('rev-parse','HEAD')
Write-Output "  local HEAD before : $(($beforeSha -split "`n")[-1])"
Write-Output "  origin/master     : $(Sh $work @('rev-parse','origin/master'))"
Write-Output "  file 'lane work' present: $(Test-Path (Join-Path $work 'b.txt'))"

Write-Output ""
Write-Output "=== Extracting the REAL block from daily_scan.ps1 ==="
$ps = Get-Content (Join-Path $repo 'daily_scan.ps1') -Raw
$startMarker = '    $aheadCount  = [int]'
$endMarker   = '    if ($localSha -ne $remoteSha) {'
$s = $ps.IndexOf($startMarker)
$e = $ps.IndexOf($endMarker)
if ($s -lt 0 -or $e -lt 0 -or $e -le $s) { Write-Output "FAIL  could not locate the block in daily_scan.ps1"; exit 1 }
$block = $ps.Substring($s, $e - $s)
Write-Output "  extracted $($block.Length) chars from the shipping script"
if ($block -notmatch 'git push origin master') { Write-Output "FAIL  block does not push"; exit 1 }
Write-Output "  block contains a push: yes"

# Harness that runs the extracted block verbatim against the throwaway repo.
$harness = Join-Path $root 'harness.ps1'
$prelude = @"
`$repo = '$work'
`$git  = '$git'
`$aheadCount=0; `$behindCount=0; `$localSha=''; `$remoteSha=''
`$pushOut=`$null; `$pubCode=0; `$prevEapPub='Continue'; `$pubOut=`$null; `$unpushed=@()
function Log(`$m) { Write-Host "  [scan] `$m" }
"@
($prelude + "`n" + $block + "`nWrite-Host '  [scan] BLOCK COMPLETED'") |
    Set-Content -Path $harness -Encoding UTF8

Write-Output ""
Write-Output "=== Running the real block (simulating the 06:31 scan) ==="
Push-Location $work
try {
    $out = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $harness 2>&1
    $out | ForEach-Object { "  $_" }
    $code = $LASTEXITCODE
} finally { Pop-Location }
Write-Output "  harness exit=$code"

Write-Output ""
Write-Output "=== VERDICT ==="
$fails = 0
$headAfter = Sh $work @('rev-parse','HEAD')
$workStillThere = Test-Path (Join-Path $work 'b.txt')
$onRemote = (Sh $work @('rev-parse','origin/master')) -eq ($headAfter -split "`n")[-1]
$inHistory = (Sh $work @('log','--oneline')) -match 'lane work not pushed'

if ($workStillThere) { Write-Output "  PASS  the lane's file survived (not reset away)" }
else { Write-Output "  FAIL  the lane's file was destroyed by the reset"; $fails++ }
if ($inHistory) { Write-Output "  PASS  the lane's commit is still in master history" }
else { Write-Output "  FAIL  the lane's commit was discarded"; $fails++ }
if ($onRemote) { Write-Output "  PASS  origin/master now carries the work (it was published, not abandoned)" }
else { Write-Output "  FAIL  origin/master does NOT carry the work"; $fails++ }

Write-Output ""
if ($fails -eq 0) {
    Write-Output "RESULT: PASS - unpushed lane work is published, never discarded"
} else {
    Write-Output "RESULT: FAIL - $fails problem(s)"
}
if ($fails -eq 0) { Remove-Item $root -Recurse -Force -ErrorAction SilentlyContinue }
exit $fails