"""Confirm: is the LIVE scanner's IV column actually the 3-day P/E upside?

Parses rowsData straight out of the served homepage and compares every row's
'iv' against 'pe_upside'. Reads the deployed artifact, not the source.
"""
import json
import re
import urllib.request

req = urllib.request.Request("https://aismarketcap.com",
                             headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=45) as r:
    html = r.read().decode("utf-8", "replace")

m = re.search(r"rowsData\s*=\s*(\[.*?\]);\s*\n", html, re.S)
if not m:
    m = re.search(r"rowsData\s*=\s*(\[.*?\]);", html, re.S)
rows = json.loads(m.group(1))

print(f"rows parsed from LIVE page: {len(rows)}\n")
print(f"{'ticker':<8}{'IV':>7}{'pe_upside':>11}{'3d':>9}{'7d':>8}   verdict")
print("-" * 58)

same_up = 0
ivs = []
for r in rows[:20]:
    iv = r.get("iv")
    up = r.get("pe_upside")
    d3 = r.get("3d")
    d7 = r.get("7d")
    if isinstance(iv, (int, float)):
        ivs.append(iv)
    verdict = ""
    if isinstance(iv, (int, float)) and isinstance(up, (int, float)):
        if abs(iv - up) < 0.05:
            verdict = "IV == pe_upside  <-- BUG"
            same_up += 1
    print(f"{r.get('ticker', '?'):<8}{str(iv):>7}{str(up):>11}{str(d3):>9}{str(d7):>8}   {verdict}")

print(f"\nrows where IV equals pe_upside: {same_up}/20")
if ivs:
    print(f"IV range on live page: {min(ivs)} - {max(ivs)}")
    print("Real pre-earnings IV for large-cap tech is typically 40-60%.")
    if max(ivs) < 20:
        print("Every value is far below a plausible IV -> column is not IV at all.")