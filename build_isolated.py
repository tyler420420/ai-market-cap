with open('ai_earnings_57day_20260519_2312.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Extract the full first script block (the one with rowsData)
s = c.find('<script>')
e = c.find('</script>')
script = c[s+8:e]

# Build isolated test page - body ONLY has table, nothing else
# This strips ALL CSS and header to isolate the JS execution issue
isolated = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Isolated Test</title>
</head>
<body>
<table id="stockTable" border="1" style="color:white">
<thead><tr>
<th>Ticker</th><th>Score</th><th>Days</th><th>Price</th>
</tr></thead>
<tbody id="stockTableBody" style="border:2px solid red">
<tr><td colspan="4" id="debug-status">Loading...</td></tr>
</tbody>
</table>
<div id="console-log" style="margin-top:20px;padding:10px;background:#222;color:#0f0;font-family:monospace;max-height:200px;overflow:auto"></div>
<script>
window.onerror = function(msg, url, line) {
    document.getElementById('debug-status').textContent = 'ERROR: ' + msg + ' at line ' + line;
    document.getElementById('debug-status').style.background = '#700';
    return true;
};
(function() {
    var log = document.getElementById('console-log');
    var origLog = console.log;
    console.log = function() {
        var args = Array.prototype.slice.call(arguments);
        log.innerHTML += '<div>' + args.map(function(a) { return String(a); }).join(' ') + '</div>';
        origLog.apply(console, arguments);
    };
})();
console.log('STEP 1: Script loaded');
console.log('STEP 2: rowsData defined: ' + (typeof rowsData !== 'undefined'));
</script>
""" + script + """
<script>
console.log('STEP 3: After main script, typeof rowsData: ' + typeof rowsData);
console.log('STEP 4: rowsData length: ' + (typeof rowsData !== 'undefined' ? rowsData.length : 'N/A'));
console.log('STEP 5: document.getElementById stockTableBody: ' + document.getElementById('stockTableBody'));
console.log('STEP 6: About to call renderTable manually...');
(function() {
    var tbody = document.getElementById('stockTableBody');
    if (!tbody) {
        console.log('FAIL: tbody not found at manual call time');
        document.getElementById('debug-status').textContent = 'FAIL: tbody not found!';
        return;
    }
    console.log('tbody found, setting innerHTML directly');
    var html = '';
    for (var i = 0; i < rowsData.length; i++) {
        var r = rowsData[i];
        html += '<tr style="background:' + (r.score >= 80 ? 'rgba(0,255,136,0.2)' : 'rgba(31,111,235,0.2)') + '">';
        html += '<td>' + r.ticker + '</td>';
        html += '<td>' + r.score + '</td>';
        html += '<td>' + r.days_left + '</td>';
        html += '<td>$' + r.price + '</td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
    console.log('SUCCESS: Set ' + rowsData.length + ' rows directly');
    document.getElementById('debug-status').textContent = 'SUCCESS: ' + rowsData.length + ' rows rendered';
    document.getElementById('debug-status').style.background = '#070';
    document.getElementById('debug-status').style.color = '#0f0';
})();
</script>
</body>
</html>"""

with open('isolated_test.html', 'w', encoding='utf-8') as f:
    f.write(isolated)

print(f'Created isolated_test.html, {len(isolated)} chars')
print(f'Script block size: {len(script)} chars')