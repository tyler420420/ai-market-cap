import json
from pathlib import Path

# Read the current clean shell
repo = Path(__file__).parent
html_file = Path(r'C:\Users\Tyler_AI\Desktop\test_scanner.html')
with open(html_file, encoding='utf-8') as f:
    html = f.read()

# Read the current data
json_file = repo / 'scanner_data.json'  # this is the live data we just downloaded
with open(json_file, encoding='utf-8') as f:
    data = json.load(f)

# Replace the loadData fetch with embedded data
# Find and replace the loadData function body
old_load = """function loadData() {
    fetch('/data')
        .then(function(r) { return r.json(); })
        .then(function(d) {
            rowsData = d;"""

new_load = f"""function loadData() {{
    rowsData = {json.dumps(data)};"""

html = html.replace(old_load, new_load)

# Remove the rest of the fetch chain (keep only the timestamp/D RAM updates)
# The .then chains after rowsData = d; need to be adjusted
# The fetch chain sets dataLoaded=true and updates lastUpdated + DRAM price
# Let's keep that part but remove the fetch call

# Find the closing of the first .then and remove the fetch boilerplate
# Actually, let me just patch it more surgically:
# The pattern after rowsData = d; is:
#             dataLoaded = true;
#             ... timestamp code ...
#             renderTable();
#             updateArrows();
#         })
#         .catch(...)
# So I need to remove the outer .then wrapper and the .catch

old_fetch_wrapper = """.then(function(d) {
            rowsData = d;
            dataLoaded = true;
            var updated = document.getElementById('lastUpdated');
            if (updated) {
                var now = new Date();
                var pt = new Date(now.toLocaleString('en-US', {timeZone: 'America/Los_Angeles'}));
                var ts = pt.toLocaleString('en-US', {timeZone: 'America/Los_Angeles', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true});
                updated.textContent = 'Last Updated: ' + ts + ' PT';
            }
            var dramRow = rowsData.find(function(r) { return r.ticker === 'DRAM'; });
            if (dramRow) {
                var dramEl = document.getElementById('dram-price');
                if (dramEl) dramEl.textContent = '$' + dramRow.price.toFixed(2);
            }
            renderTable();
            updateArrows();
        })
        .catch(function(e) {
            console.error('Failed to load data:', e);
            var tbody = document.getElementById('stockTableBody');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="19" style="text-align:center;padding:30px;color:#ff6b6b">Failed to load data. Please refresh.</td></tr>';
            }
        });"""

new_fetch_wrapper = """var updated = document.getElementById('lastUpdated');
            if (updated) {
                var now = new Date();
                var pt = new Date(now.toLocaleString('en-US', {timeZone: 'America/Los_Angeles'}));
                var ts = pt.toLocaleString('en-US', {timeZone: 'America/Los_Angeles', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true});
                updated.textContent = 'Last Updated: ' + ts + ' PT';
            }
            var dramRow = rowsData.find(function(r) { return r.ticker === 'DRAM'; });
            if (dramRow) {
                var dramEl = document.getElementById('dram-price');
                if (dramEl) dramEl.textContent = '$' + dramRow.price.toFixed(2);
            }
            renderTable();
            updateArrows();"""

html = html.replace(old_fetch_wrapper, new_fetch_wrapper)

with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Updated test_scanner.html with {len(data)} stocks embedded')
print(f'File size: {len(html)} bytes')
for r in data[:3]:
    print(f'  {r["ticker"]} - {r["company_name"][:40]} - score {r["score"]}')
