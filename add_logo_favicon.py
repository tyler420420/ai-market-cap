content = open('ai_earnings_today.html', encoding='utf-8').read()

# 1. Add meta tags in head
old_head = '<title>AI Market Cap Scanner</title><style>'
new_head = '''<title>AI Market Cap Scanner</title>
<link rel="icon" type="image/png" href="/static/logo.png">
<meta name="description" content="AI pre-earnings momentum scanner for tech stocks. Track scores, analyst ratings, PE targets, and implied moves before earnings reports.">
<meta property="og:title" content="AI Market Cap Scanner">
<meta property="og:description" content="Pre-earnings momentum scanner for AI/tech stocks. Scores, PE targets, 3-day and 5-day implied moves.">
<meta property="og:type" content="website">
<style>'''
if old_head in content:
    content = content.replace(old_head, new_head)
    print('1. Added meta tags')
else:
    print('1. NOT found')

# 2. Add logo in header replacing h1 text
old_header = '<div class=hdr-row><div><h1>AI Market Cap Scanner</h1>'
new_header = '<div class=hdr-row><div><img src="file:///C:\\Users\\Tyler_AI\\Desktop\\AI_Market_Cap_Logo3.png" height="55" style="vertical-align:middle;margin-right:12px"><span style="color:#58a6ff;font-size:1.6em;font-weight:bold">AI Market Cap</span>'
if old_header in content:
    content = content.replace(old_header, new_header)
    print('2. Added logo')
else:
    print('2. NOT found')

# 3. Better "last updated" text
old_updated = "Updated:"
new_updated = "Last Updated:"
if old_updated in content:
    content = content.replace(old_updated, new_updated)
    print('3. Updated timestamp label')
else:
    print('3. Already updated')

with open('ai_earnings_today.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')