with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# The updateArrows function as it currently appears
old = "function updateArrows(){document.querySelectorAll('th[data-col]').forEach(function(th){th.classList.remove('sorted-asc','sorted-desc');});var th=document.querySelector('th[data-col=\"'+sortCol+'\"]');if(th){th.classList.add(sortAsc?'sorted-asc':'sorted-desc');}}"

# Try to find it
if old in c:
    print('Found exact match')
else:
    print('Not found - checking what IS there')
    idx = c.find('function updateArrows')
    print(repr(c[idx:idx+250]))