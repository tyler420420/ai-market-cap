import requests, re, json
r = requests.get('https://aismarketcap.com', timeout=15)
c = r.text
m = re.search(r'rowsData\s*=\s*(\[.*?\]);\s*var', c, re.DOTALL)
data = json.loads(m.group(1))
sb = [s for s in data if s.get('score', 0) >= 75]
watch = [s for s in data if 50 <= s.get('score', 0) < 75]
print(f"Strong Buy: {len(sb)}")
print(f"Watch: {len(watch)}")
scores = sorted([s.get('score', 0) for s in data])
print(f"Top 5 scores: {scores[-5:]}")
print(f"Bottom 5 scores: {scores[:5]}")
print(f"Total stocks: {len(data)}")