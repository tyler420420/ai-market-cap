with open('ai_earnings_tight.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Add glow CSS for strong buy rows and featured banner
glow_css = '''@keyframes sb-glow{0%,100%{box-shadow:0 0 4px rgba(63,185,80,.3)}50%{box-shadow:0 0 10px rgba(63,185,80,.6)}}tr[style*="rgba(0,255,136,0.12)"]{animation:sb-glow 2.5s ease-in-out infinite;border-left:3px solid #3fb950}@keyframes feat-glow{0%,100%{box-shadow:0 0 6px rgba(63,185,80,.4)}50%{box-shadow:0 0 20px rgba(63,185,80,.7)}}'''

# Update pick banner with stronger glow
c = c.replace('class=pick-banner style="background:linear-gradient(135deg,#0d2b1a,#162016);border:1px solid #2ea043;border-radius:8px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px"',
              'class=pick-banner style="background:linear-gradient(135deg,#0d2b1a,#142814);border:2px solid #3fb950;border-radius:14px;padding:24px 28px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin:12px 0;animation:feat-glow 2s ease-in-out infinite"')

# Remove old glow CSS and add new
old_glow = '@keyframes sb-glow{0%,100%{box-shadow:0 0 4px rgba(63,185,80,.3)}50%{box-shadow:0 0 12px rgba(63,185,80,.7)}}tr:has(.sb-glow){animation:sb-glow 2.5s ease-in-out infinite;border-left:3px solid #3fb950}'
c = c.replace(old_glow, glow_css)

open('ai_earnings_tight.html', 'w', encoding='utf-8').write(c)
print('Done')