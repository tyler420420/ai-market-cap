with open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'r', encoding='utf-8') as f:
    h = f.read()

# FAQ: yellow bg, black text -> yellow bg, white text
h = h.replace(
    "background:#ffd700;color:#000;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff\" onmouseover=\"this.style.background='#fff176'\" onmouseout=\"this.style.background='#ffd700'\">FAQ</a>",
    "background:#ffd700;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff\" onmouseover=\"this.style.background='#fff176'\" onmouseout=\"this.style.background='#ffd700'\">FAQ</a>"
)

# PRO SCAN: green bg, black text -> green bg, white text
h = h.replace(
    "background:#00ff88;color:#000;font-weight:bold;border:1px solid #fff;cursor:pointer\" onmouseover=\"this.style.background='#79ffc6'\" onmouseout=\"this.style.background='#00ff88'\" onclick=runScan()>PRO SCAN</button>",
    "background:#00ff88;color:#fff;font-weight:bold;border:1px solid #fff;cursor:pointer\" onmouseover=\"this.style.background='#79ffc6'\" onmouseout=\"this.style.background='#00ff88'\" onclick=runScan()>PRO SCAN</button>"
)

with open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(h)
print("Done")
