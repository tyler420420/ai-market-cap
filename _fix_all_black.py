with open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'r', encoding='utf-8') as f:
    h = f.read()

# FAQ: yellow bg, white text -> yellow bg, black text
h = h.replace(
    "background:#ffd700;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff\" onmouseover=\"this.style.background='#fff176'\" onmouseout=\"this.style.background='#ffd700'\">FAQ</a>",
    "background:#ffd700;color:#000;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff\" onmouseover=\"this.style.background='#fff176'\" onmouseout=\"this.style.background='#ffd700'\">FAQ</a>"
)

# Wins: blue bg, white text -> blue bg, black text
h = h.replace(
    "background:#58a6ff;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff\" onmouseover=\"this.style.background='#79b8ff'\" onmouseout=\"this.style.background='#58a6ff'\">Wins</a>",
    "background:#58a6ff;color:#000;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff\" onmouseover=\"this.style.background='#79b8ff'\" onmouseout=\"this.style.background='#58a6ff'\">Wins</a>"
)

# PRO SCAN: green bg, white text -> green bg, black text
h = h.replace(
    "background:#00ff88;color:#fff;font-weight:bold;border:1px solid #fff;cursor:pointer\" onmouseover=\"this.style.background='#79ffc6'\" onmouseout=\"this.style.background='#00ff88'\" onclick=runScan()>PRO SCAN</button>",
    "background:#00ff88;color:#000;font-weight:bold;border:1px solid #fff;cursor:pointer\" onmouseover=\"this.style.background='#79ffc6'\" onmouseout=\"this.style.background='#00ff88'\" onclick=runScan()>PRO SCAN</button>"
)

# Follow Us On X: purple bg, white text -> purple bg, black text
h = h.replace(
    "background:#5741d9;color:#fff;padding:3px 10px;border-radius:5px;border:1px solid #fff;font-size:0.82em;font-weight:bold;text-decoration:none\" onmouseover=\"this.style.background='#6e55e0'\" onmouseout=\"this.style.background='#5741d9'\">Follow Us On X</a>",
    "background:#5741d9;color:#000;padding:3px 10px;border-radius:5px;border:1px solid #fff;font-size:0.82em;font-weight:bold;text-decoration:none\" onmouseover=\"this.style.background='#6e55e0'\" onmouseout=\"this.style.background='#5741d9'\">Follow Us On X</a>"
)

with open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(h)
print("All 4 buttons: black text ✅")
