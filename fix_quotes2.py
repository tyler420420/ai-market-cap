with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# The current (broken) selector string inside a double-quoted Python string
# In Python "": \" produces a literal quote
# So "th[data-col=\"'+sortCol+'\"]" has value: th[data-col="'+sortCol+'"]
# But when this is written to HTML and browser parses JS: 'th[data-col="'+sortCol+'"]'
# Inside JS single-quoted string: "'+sortCol+'" becomes concatenated sortCol value
# Result: 'th[data-col='+value+']' which gives th[data-col=VALUE]

# Fix: Use \\" in Python to produce \" in the string value
# Then in HTML JS: 'th[data-col=\"'+sortCol+'"]'
# JS parsing: 'th[data-col="' becomes "th[data-col=", sortCol is variable, '+'"]'
# Result: 'th[data-col="'+VALUE+'"]'

old = 'th[data-col="\'+sortCol+\'"]'
new = 'th[data-col=\\\'"+sortCol+"\\\']'

if old in c:
    print('Found')
    c2 = c.replace(old, new, 1)
    with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
        f.write(c2)
    print('Fixed')
else:
    print('Not found')