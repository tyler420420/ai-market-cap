with open('ai_earnings_tight.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Stronger glow CSS for pick banner
glow_css = '@keyframes sb-glow{0%,100%{box-shadow:0 0 4px rgba(63,185,80,.3)}50%{box-shadow:0 0 12px rgba(63,185,80,.7)}}tr[style*="rgba(0,255,136,0.12)"]{animation:sb-glow 2.5s ease-in-out infinite;border-left:3px solid #3fb950}'
c = c.replace('</style>', glow_css + '</style>')

# Change pick banner styling - brighter gradient with glow
c = c.replace('class=pick-banner style="background:linear-gradient(135deg,#0d2b1a,#162016);border:1px solid #2ea043;border-radius:8px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px"',
              'class=pick-banner style="background:linear-gradient(135deg,#0d2b1a,#142814);border:2px solid #3fb950;border-radius:14px;padding:24px 28px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin:12px 0;box-shadow:0 0 20px rgba(63,185,80,.25),inset 0 1px 0 rgba(63,185,80,.1);animation:sb-glow 3s ease-in-out infinite"')

open('ai_earnings_tight.html', 'w', encoding='utf-8').write(c)
print('Done')