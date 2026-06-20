with open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'r', encoding='utf-8') as f:
    h = f.read()

# Find the Calendar button text and remove the whole <a> tag
old = '<a href="/calendar" style="background:#1f6feb;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff" onmouseover="this.style.background=\'#388bfd\'" onmouseout="this.style.background=\'#1f6feb\'">Calendar</a>'
new = ''

if old in h:
    h = h.replace(old, new)
    print("Calendar button removed!")
else:
    # Try without escaped quotes
    old2 = '<a href="/calendar"'
    if old2 in h:
        idx = h.find(old2)
        end = h.find('</a>', idx) + 4
        h = h[:idx] + h[end:]
        print("Calendar button removed (alt method)!")
    else:
        print("Calendar button not found")

with open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(h)
