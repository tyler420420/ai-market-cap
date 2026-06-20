with open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'r', encoding='utf-8') as f:
    h = f.read()

# FAQ: red -> yellow
h = h.replace(
    "background:#dc3545;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff\" onmouseover=\"this.style.background='#e84a5f'\" onmouseout=\"this.style.background='#dc3545'\">FAQ</a>",
    "background:#ffd700;color:#000;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff\" onmouseover=\"this.style.background='#fff176'\" onmouseout=\"this.style.background='#ffd700'\">FAQ</a>"
)

# Wins: green -> blue
h = h.replace(
    "background:#238636;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff\" onmouseover=\"this.style.background='#2ea043'\" onmouseout=\"this.style.background='#238636'\">Wins</a>",
    "background:#58a6ff;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff\" onmouseover=\"this.style.background='#79b8ff'\" onmouseout=\"this.style.background='#58a6ff'\">Wins</a>"
)

# PRO SCAN: yellow -> green
h = h.replace(
    "style=\"background:#ffd700;color:#000;font-weight:bold;border:1px solid #fff;cursor:pointer\" onmouseover=\"this.style.background='#fff176'\" onmouseout=\"this.style.background='#ffd700'\" onclick=runScan()>PRO SCAN</button>",
    "style=\"background:#00ff88;color:#000;font-weight:bold;border:1px solid #fff;cursor:pointer\" onmouseover=\"this.style.background='#79ffc6'\" onmouseout=\"this.style.background='#00ff88'\" onclick=runScan()>PRO SCAN</button>"
)

with open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(h)

# Verify
with open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'r', encoding='utf-8') as f:
    h2 = f.read()

if "#ffd700" in h2 and "FAQ" in h2:
    print("FAQ: yellow ✅")
if "#58a6ff" in h2 and "Wins</a>" in h2:
    print("Wins: blue ✅")
if "#00ff88" in h2 and "PRO SCAN" in h2:
    print("PRO SCAN: green ✅")
if "#dc3545" in h2:
    print("WARNING: red still present")
if "#238636" in h2:
    print("WARNING: old green still present")
