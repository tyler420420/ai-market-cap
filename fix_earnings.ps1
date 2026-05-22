$c = Get-Content 'ai_earnings_today.html' -Raw
$c = $c -replace 'color:#ffcc00">1 days', 'color:#00ff88">1 days'
Set-Content 'ai_earnings_today.html' $c -Encoding UTF8
Write-Host 'Done'