c=open(r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html').read()
# Find the Watch badge in the header section (near the Strong Buy badge)
i=c.find('color:#58a6ff">', c.find('8b949e">Strong Buy'))
print(c[i:i+60])
