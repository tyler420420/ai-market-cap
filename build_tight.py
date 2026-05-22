# Tighten up the original source - minimal changes only
import re

with open('ai_earnings_57day_20260520_0227.html', 'r', encoding='utf-8') as f:
    src = f.read()

# Extract all parts
css_start = src.find('<style>') + 7
css_end = src.find('</style>')
css = src[css_start:css_end]

# Get everything after CSS
body_and_scripts = src[css_end+8:]

# ===== TIGHTEN CSS =====
# Remove padding/margin bloat while keeping everything else
tight_css = css
tight_css = tight_css.replace('body{font-family:Segoe UI,Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:20px}', 
                              'body{font-family:Segoe UI,Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:12px}')
tight_css = tight_css.replace('.header{padding:25px;border-radius:12px;margin-bottom:20px}', 
                              '.header{padding:18px 20px;border-radius:10px;margin-bottom:12px}')
tight_css = tight_css.replace('.stats-bar{margin:15px 0}', 
                              '.stats-bar{margin:10px 0}')
tight_css = tight_css.replace('td{padding:18px 12px', 
                              'td{padding:10px 10px')
tight_css = tight_css.replace('th{padding:10px 12px', 
                              'th{padding:8px 10px')
tight_css = tight_css.replace('html += \'*{margin:0;padding:0;box-sizing:border-box}body{font-family:Segoe UI,Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:20px}\'', 
                              '')
tight_css = tight_css.replace('.updated{margin-top:12px', 
                              '.updated{margin-top:8px')
tight_css = tight_css.replace('note{margin-top:20px', 
                              'note{margin-top:12px')
tight_css = tight_css.replace('disclaimer{margin-top:12px', 
                              'disclaimer{margin-top:8px')
tight_css = tight_css.replace('.stat{padding:12px 18px', 
                              '.stat{padding:10px 14px')
tight_css = tight_css.replace('table{width:100%;border-collapse:collapse;background:#161b22;border-radius:8px;overflow:hidden;margin-top:10px}', 
                              'table{width:100%;border-collapse:collapse;background:#161b22;border-radius:8px;overflow:hidden;margin-top:6px}')
tight_css = tight_css.replace('.ticker-strip{padding:8px 0', 
                              '.ticker-strip{padding:6px 0')
tight_css = tight_css.replace('.ticker-item{padding:0 18px', 
                              '.ticker-item{padding:0 14px')
tight_css = tight_css.replace('tr{height:54px}', 
                              'tr{height:auto}')
tight_css = tight_css.replace('#chat-panel{max-height:520px', 
                              '#chat-panel{max-height:450px')
tight_css = tight_css.replace('#chat-msgs{max-height:340px', 
                              '#chat-msgs{max-height:300px')
tight_css = tight_css.replace('#chat-header{padding:14px 16px', 
                              '#chat-header{padding:12px 14px')
tight_css = tight_css.replace('#chat-msgs{padding:14px 16px', 
                              '#chat-msgs{padding:12px 14px')

# ===== ADD RESPONSIVE =====
responsive = """
@media(max-width:900px){body{padding:8px}.header{padding:14px 16px;border-radius:8px;margin-bottom:10px}h1{font-size:1.4em}.stat{padding:8px 12px}.pick-banner{padding:14px 16px}.note,.disclaimer{margin-top:8px;padding:10px 14px}}
@media(max-width:600px){body{padding:6px}.hdr-row{flex-direction:column;align-items:start}.btn{padding:8px 16px;font-size:.82em}table{min-width:600px}th,td{padding:7px 8px;font-size:.75em}.pick-banner{flex-direction:column;gap:8px;padding:12px 14px}}
"""

# Insert responsive before </style>
tight_css = tight_css + responsive

# ===== BUILD NEW FILE =====
new_html = "<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>AI Market Cap Scanner</title><style>" + tight_css + "</style></head><body>" + body_and_scripts

with open('ai_earnings_tight.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("Done! Size:", len(new_html))