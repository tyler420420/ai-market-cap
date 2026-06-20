import re

with open('ai_earnings_today.html', 'r', encoding='utf-8') as f:
    h = f.read()

# Find all days cells with colors
# Pattern: data-label="Days"><span style="color:#xxxxxx">NNd</span>
pattern = r'data-label="Days"><span style="color:([^"]+)">([^<]+)</span>'
matches = re.findall(pattern, h)

from collections import Counter
counts = Counter(matches)
print("Days color distribution in static rows:")
for (color, days), count in sorted(counts.items(), key=lambda x: x[0][1]):
    print(f"  {color} ({days}): {count}")

# Also check total rows
print(f"\nTotal static rows with days: {len(matches)}")

# Spot check: MU should be 5d = yellow (#ffcc00), GOOG 34d = green (#00ff88)
print("\nSpot checks:")
for t in ['MU', 'GOOG', 'CBRS', 'ASML', 'NFLX']:
    m = re.search(rf'<td data-label="Ticker"><strong><a href="[^"]+{t}"[^>]+>[^<]+</a></strong></td><td[^>]+>[^<]+</td><td[^>]+>[^<]+</td><td[^>]+>[^<]+</td><td data-label="Days"><span style="color:([^"]+)">([^<]+)</span>', h)
    if m:
        print(f"  {t}: color={m.group(1)}, days={m.group(2)}")
