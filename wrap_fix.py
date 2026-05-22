c = open('ai_earnings_today.html', encoding='utf-8').read()

# Find the body opening and wrap everything in a container div
old = "<body>"
new = "<body><div style='max-width:1400px;margin:0 auto'>"

# Close the container at end of body before </body>
old2 = "</body>"
new2 = "</div></body>"

if old in c:
    c = c.replace(old, new, 1)
    c = c.replace(old2, new2, 1)
    open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
    print('Done - wrapper added')
else:
    print('NOT found')