with open('ai_earnings_tight.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Add glow CSS
glow_css = '@keyframes sb-glow{0%,100%{box-shadow:0 0 4px rgba(63,185,80,.3)}50%{box-shadow:0 0 12px rgba(63,185,80,.7)}}tr:has(.sb-glow){animation:sb-glow 2.5s ease-in-out infinite;border-left:3px solid #3fb950;}'
c = c.replace('</style>', glow_css + '</style>')

# Add sb-glow class to cells with the green color (strong buy values)
c = c.replace('<td style="color:#00ff88">', '<td class="sb-glow" style="color:#00ff88">')

open('ai_earnings_tight.html', 'w', encoding='utf-8').write(c)
print('Done')