content = open(r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html', 'r', encoding='utf-8').read()

# Footer nav to insert before </body>
footer = """<div style="background:#161b22;border-top:1px solid #30363d;padding:16px 24px;display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin-top:20px"><a href="/blog" style="background:#e63946;color:#fff;padding:10px 20px;border-radius:6px;font-size:0.88em;text-decoration:none;font-weight:bold;onmouseover='this.style.background=\"#ff6b6b\"' onmouseout='this.style.background=\"#e63946\"'">Blog</a><a href="/pricing" style="background:#238636;color:#fff;padding:10px 20px;border-radius:6px;font-size:0.88em;text-decoration:none;font-weight:bold;onmouseover='this.style.background=\"#2ea043\"' onmouseout='this.style.background=\"#238636\"'">Subscribe</a><a href="/wins" style="background:#58a6ff;color:#000;padding:10px 20px;border-radius:6px;font-size:0.88em;text-decoration:none;font-weight:bold;onmouseover='this.style.background=\"#79b8ff\"' onmouseout='this.style.background=\"#58a6ff\"'">Wins</a></div>"""

# Insert before </body>
old_end = '</body></html>'
new_end = footer + '\n</body></html>'

if old_end in content:
    content = content.replace(old_end, new_end, 1)
    open(r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html', 'w', encoding='utf-8').write(content)
    print('Done - footer added')
else:
    print('Could not find </body></html>')
