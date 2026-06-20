import urllib.request, json

# Check what the local Flask server returns
url = 'http://localhost:18765/data'
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read())
    print(f'Local Flask: {len(data)} stocks')
    for r in data[:3]:
        print(f'  {r["ticker"]} - {r["company_name"]} - score {r["score"]}')
except Exception as e:
    print(f'Local Flask unreachable: {e}')

# Check Desktop test file location
import os
desktop = r'C:\Users\Tyler_AI\Desktop\test_scanner.html'
size = os.path.getsize(desktop)
print(f'\nDesktop test_scanner.html: {size} bytes')
