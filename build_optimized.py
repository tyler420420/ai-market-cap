# Extract key sections from source HTML and build optimized version
import re

with open('ai_earnings_57day_20260520_0227.html', 'r', encoding='utf-8') as f:
    src = f.read()

# Extract CSS block
css_start = src.find('<style>') + 7
css_end = src.find('</style>')
css = src[css_start:css_end]

# Extract rowsData JSON
json_start = src.find('var rowsData=') + 13
json_end = src.find(';', json_start)
rows_json = src[json_start:json_end+1]

# Extract everything after the CSS closing tag until end (we'll keep all scripts)
html_content_start = css_end + 8  # after </style>

# ===== NEW OPTIMIZED CSS =====
new_css = """
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#0a0e14;color:#e6edf3;padding:0;min-height:100vh}
.wrap{max-width:1400px;margin:0 auto;padding:20px}

/* HEADER */
.header{background:linear-gradient(145deg,#131922 0%,#1a2332 100%);border:1px solid #30363d;border-radius:16px;padding:28px 32px;margin-bottom:16px;box-shadow:0 4px 24px rgba(0,0,0,.4)}
.hdr-row{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px}
.hdr-left{display:flex;flex-direction:column;gap:4px}
h1{color:#58a6ff;font-size:1.6em;font-weight:700;letter-spacing:-.02em}
.desc{color:#8b949e;font-size:.85em}
.hdr-right{display:flex;gap:10px;align-items:center}
.btn{background:#2ea043;border:none;color:#fff;padding:9px 20px;border-radius:8px;font-size:.85em;font-weight:600;cursor:pointer;transition:all .15s;box-shadow:0 2px 8px rgba(46,160,67,.25)}
.btn:hover{background:#3fb950;transform:translateY(-1px);box-shadow:0 4px 12px rgba(46,160,67,.35)}
.btn:disabled{background:#21262d;color:#484f58;cursor:not-allowed;transform:none;box-shadow:none}
#refreshBtn{background:#1f6feb;box-shadow:0 2px 8px rgba(31,111,235,.25)}
#refreshBtn:hover{background:#388bfd;box-shadow:0 4px 12px rgba(31,111,235,.35)}

/* TICKER */
.ticker-strip{background:#080c12;border-bottom:1px solid #21262d;padding:10px 0;font-size:.78em;overflow:hidden}
.ticker-strip-inner{display:flex;width:max-content}
.ticker-item{display:inline-flex;align-items:center;gap:8px;padding:0 24px;border-right:1px solid #21262d;white-space:nowrap}
.ticker-sym{font-weight:700;color:#58a6ff}
.ticker-price{color:#8b949e}
.ticker-up{color:#3fb950}
.ticker-dn{color:#f85149}
@keyframes scroll-ticker{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
.ticker-strip:hover .ticker-strip-inner{animation-play-state:paused}

/* AI PICK BANNER */
.pick-banner{background:linear-gradient(135deg,#0d2b1a 0%,#162016 100%);border:1px solid #238636;border-radius:14px;padding:24px 28px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:16px;box-shadow:0 0 24px rgba(35,134,54,.15)}
.pick-badge{background:#238636;color:#fff;padding:4px 12px;border-radius:20px;font-size:.7em;font-weight:700;text-transform:uppercase;letter-spacing:.05em}
.pick-ticker{color:#fff;font-size:1.4em;font-weight:700}
.pick-name{color:#8b949e;font-size:.85em}
.pick-meta{display:flex;gap:16px;flex-wrap:wrap}
.pick-meta span{color:#8b949e;font-size:.82em}
.pick-meta strong{color:#fff}
.pick-meta .green{color:#3fb950;font-weight:700}
.pick-meta .yellow{color:#d29922;font-weight:700}
.pick-meta .blue{color:#58a6ff;font-weight:700}

/* STATS BAR */
.stats-bar{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px}
.legend{display:flex;gap:18px;font-size:.8em;flex-wrap:wrap}
.legend span{display:flex;align-items:center;gap:6px;color:#8b949e}
.dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.stat{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:10px 16px;text-align:center;min-width:80px}
.stat-val{font-size:1.3em;font-weight:700;color:#58a6ff}
.stat-lbl{font-size:.68em;color:#6e7681;text-transform:uppercase;letter-spacing:.05em;margin-top:2px}

/* TABLE */
.table-wrap{overflow-x:auto;border-radius:12px;border:1px solid #30363d;background:#161b22;margin-bottom:20px;box-shadow:0 4px 16px rgba(0,0,0,.3)}
table{width:100%;border-collapse:collapse;min-width:900px}
thead{background:#0d1117;position:sticky;top:0;z-index:10}
th{padding:12px 14px;text-align:left;font-size:.72em;color:#8b949e;text-transform:uppercase;letter-spacing:.06em;font-weight:600;border-bottom:2px solid #30363d;white-space:nowrap;cursor:pointer;user-select:none;transition:color .15s}
th:hover{color:#e6edf3}
th.sorted-asc{color:#3fb950}
th.sorted-asc::after{content:" ▲";font-size:.85em}
th.sorted-desc{color:#3fb950}
th.sorted-desc::after{content:" ▼";font-size:.85em}
td{padding:14px 14px;border-bottom:1px solid #21262d;font-size:.85em;white-space:nowrap}
tr{transition:background .12s}
tr:hover td{background:#1c2128}
tr:last-child td{border-bottom:none}
.score-strong{color:#3fb950;font-weight:700}
.score-watch{color:#58a6ff;font-weight:700}
.ticker-link{color:#58a6ff;font-weight:600;text-decoration:none}
.ticker-link:hover{text-decoration:underline}
.days-green{color:#3fb950;font-weight:700}
.days-yellow{color:#d29922;font-weight:700}
.sb-val{color:#3fb950;font-weight:600}
.buy-val{color:#58a6ff;font-weight:600}
.hold-val{color:#d29922;font-weight:600}
.sell-val{color:#f85149;font-weight:600}
.news-link{color:#e6edf3;text-decoration:none;font-size:.8em;max-width:200px;display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.news-link:hover{text-decoration:underline}

/* FOOTER */
.footer-note{margin-top:20px;padding:14px 20px;background:#161b22;border:1px solid #30363d;border-radius:10px;font-size:.78em;color:#6e7681;line-height:1.6}
.footer-note b{color:#8b949e}
.disclaimer{background:#1a1210;border-color:#f8514966;margin-top:10px;color:#6e7681}
.disclaimer b{color:#f85149}

/* CHAT */
#chat-btn{position:fixed;bottom:24px;right:24px;background:#238636;color:#fff;border:none;border-radius:10px;padding:12px 20px;font-size:.9em;font-weight:600;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,.5);z-index:9999;transition:all .2s}
#chat-btn:hover{background:#3fb950;transform:translateY(-2px)}
#chat-panel{position:fixed;bottom:80px;right:24px;width:340px;max-height:480px;background:#161b22;border:1px solid #30363d;border-radius:14px;box-shadow:0 8px 32px rgba(0,0,0,.6);display:none;flex-direction:column;z-index:9998;overflow:hidden}
#chat-panel.open{display:flex}
#chat-header{background:#0d1117;padding:14px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #30363d}
#chat-header span{font-weight:600;color:#58a6ff}
#chat-close{background:none;border:none;color:#8b949e;font-size:1.1em;cursor:pointer;padding:2px 6px}
#chat-close:hover{color:#fff}
#chat-msgs{flex:1;overflow-y:auto;padding:14px 16px;display:flex;flex-direction:column;gap:10px;min-height:180px;max-height:320px}
.msg{font-size:.85em;line-height:1.5;padding:10px 14px;border-radius:10px;max-width:85%}
.msg-user{background:#238636;color:#fff;align-self:flex-end;border-bottom-right-radius:4px}
.msg-bot{background:#1c2128;color:#e6edf3;align-self:flex-start;border-bottom-left-radius:4px}
.msg-bot.loading{color:#6e7681;font-style:italic}
#chat-input-row{display:flex;border-top:1px solid #30363d;padding:10px 12px;gap:8px}
#chat-input{flex:1;background:#0d1117;border:1px solid #30363d;border-radius:8px;color:#e6edf3;padding:8px 12px;font-size:.85em;outline:none;font-family:inherit;resize:none}
#chat-input:focus{border-color:#58a6ff}
#chat-send{background:#238636;color:#fff;border:none;border-radius:8px;padding:8px 16px;font-size:.85em;font-weight:600;cursor:pointer}
#chat-send:hover{background:#3fb950}

/* WARN */
.warn{margin-top:12px;padding:12px 16px;background:#1c2128;border-left:3px solid #d29922;border-radius:6px;font-size:.8em;color:#8b949e;display:none}
.updated{margin-top:10px;color:#6e7681;font-size:.8em}

/* RESPONSIVE */
@media (max-width:900px){
  .wrap{padding:12px}
  .header{padding:20px;border-radius:12px}
  h1{font-size:1.3em}
  .stat{padding:8px 12px;min-width:70px}
  .stat-val{font-size:1.1em}
  .pick-banner{padding:18px 20px}
  .pick-ticker{font-size:1.2em}
  th,td{padding:10px 10px;font-size:.78em}
}
@media (max-width:600px){
  .wrap{padding:8px}
  .header{padding:16px;border-radius:10px}
  .hdr-row{gap:10px}
  h1{font-size:1.1em}
  .btn{padding:8px 14px;font-size:.8em}
  .pick-banner{gap:10px;padding:14px 16px}
  .pick-ticker{font-size:1em}
  .pick-meta{gap:10px}
  .stat{padding:6px 10px;min-width:60px}
  .stat-val{font-size:1em}
  .legend{gap:12px}
  .table-wrap{border-radius:8px}
  th,td{padding:8px 8px;font-size:.72em}
  #chat-panel{width:calc(100vw-32px);right:-4px}
}
"""

# Extract HTML body (everything between </style> and <script>var rowsData)
body_start = html_content_start
body_end = src.find('<script>var rowsData=')
body_content = src[body_start:body_end]

# Extract all scripts
scripts = []
remaining = body_end
while True:
    s_open = src.find('<script>', remaining)
    if s_open < 0: break
    s_close = src.find('</script>', s_open)
    if s_close < 0: break
    scripts.append(src[s_open:s_close+9])
    remaining = s_close + 9

# ===== BUILD NEW HTML =====
new_html = "<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>AI Market Cap Scanner</title>"
new_html += "<style>" + new_css.strip() + "</style>"
new_html += "</head><body><div class='wrap'>"
new_html += body_content
new_html += "</div>"
for s in scripts:
    new_html += s
new_html += "</body></html>"

# Write output
with open('ai_earnings_optimized.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("Done! Output: ai_earnings_optimized.html")
print("Size:", len(new_html), "bytes")