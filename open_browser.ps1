$json = '{"url":"file:///C:/Users/Tyler_AI/Desktop/test_scanner.html","active":true}'
$result = & mavis browser tool open_tab $json 2>&1
Write-Output $result