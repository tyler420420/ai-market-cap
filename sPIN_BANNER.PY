with open('ai_earnings_tight.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Add spinning border animation CSS
spin_css = '''
@keyframes border-glow{0%{border-color:#3fb950;box-shadow:0 0 8px rgba(63,185,80,.4),0 0 20px rgba(63,185,80,.2)}33%{border-color:#2ea043;box-shadow:0 0 15px rgba(46,160,67,.5),0 0 30px rgba(46,160,67,.3)}66%{border-color:#3fb950;box-shadow:0 0 8px rgba(63,185,80,.4),0 0 20px rgba(63,185,80,.2)}100%{border-color:#3fb950;box-shadow:0 0 8px rgba(63,185,80,.4),0 0 20px rgba(63,185,80,.2)}}
@keyframes sb-glow{0%,100%{box-shadow:0 0 4px rgba(63,185,80,.3)}50%{box-shadow:0 0 12px rgba(63,185,80,.7)}tr[style*="rgba(0,255,136,0.12)"]{animation:sb-glow 2.5s ease-in-out infinite;border-left:3px solid #3fb950}}
'''

# Update pick banner with spinning glow
c = c.replace('animation:sb-glow 3s ease-in-out infinite"', 
              'animation:border-glow 2s ease-in-out infinite"')

# Remove the glow CSS and add the new full CSS
c = c.replace('@keyframes sb-glow{0%,100%{box-shadow:0 0 4px rgba(63,185,80,.3)}50%{box-shadow:0 0 12px rgba(63,185,80,.7)}}tr[style*="rgba(0,255,136,0.12)"]{animation:sb-glow 2.5s ease-in-out infinite;border-left:3px solid #3fb950}', spin_css)

open('ai_earnings_tight.html', 'w', encoding='utf-8').write(c)
print('Done')