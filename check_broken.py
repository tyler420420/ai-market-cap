# Read the file and find the exact content of line 534
c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
# Find the full HTML += "..." block that has the JS
# The issue: multiple partial replacements left junk. Let's find the exact broken fmtEdate
idx=c.find('fmtEdate')
print('fmtEdate at:', idx)
# Print context around it
print(repr(c[idx-50:idx+400]))