content = open('ai_earnings_today.html', encoding='utf-8').read()

# 1. Add meta tags after title
old_head = '<title>AI Market Cap Scanner</title><style>'
new_head = '<title>AI Market Cap Scanner</title>\n<link rel="icon" type="image/png" href="file:///C:/Users/Tyler_AI/Desktop/AI_Market_Cap_Logo3.png">\n<meta name="description" content="AI pre-earnings momentum scanner for tech stocks. Track scores, analyst ratings, PE targets, and implied moves before earnings reports.">\n<meta property="og:title" content="AI Market Cap Scanner">\n<meta property="og:description" content="Pre-earnings momentum scanner for AI/tech stocks. Scores, PE targets, 3-day and 5-day implied moves.">\n<style>'
if old_head in content:
    content = content.replace(old_head, new_head)
    print('1. Meta tags added')

# 2. Fix desc
old_desc = 'Pre-earnings momentum scanner for Tech sector | Auto-runs daily at 6:30 AM PT | Subscribe to unlock Run Scan & Chat'
new_desc = 'Pre-earnings momentum scanner for Tech sector'
if old_desc in content:
    content = content.replace(old_desc, new_desc)
    print('2. Desc fixed')

# 3. Fix title - find exact pattern
idx = content.find('AI Market Cap</span>')
if idx >= 0:
    snippet = content[idx-30:idx+30]
    # Replace from before the img tag to after the span
    start_idx = content.find('<img src="file:///C:\\Users\\Tyler_AI\\Desktop\\AI_Market_Cap_Logo3.png"', idx-50)
    if start_idx < 0:
        start_idx = content.find('"file:///C:/Users/Tyler_AI/Desktop/AI_Market_Cap_Logo3.png"', idx-50)
    if start_idx >= 0:
        end_idx = content.find('</span>', idx) + len('</span>')
        # Find the closing div of this div
        chunk = content[start_idx:end_idx]
        new_chunk = '<a href="https://aismarketcap.com" style="color:#58a6ff;text-decoration:none"><h1>AI Market Cap Scanner</h1></a><div class=desc>Pre-earnings momentum scanner for Tech sector</div>'
        content = content[:start_idx] + new_chunk + content[end_idx:]
        print('3. Title fixed')

with open('ai_earnings_today.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')