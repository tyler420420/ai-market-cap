with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Add updateArrows function after sortBy
old = "function sortBy(col){if(sortCol===col){sortAsc=!sortAsc;"
new = "function updateArrows(){document.querySelectorAll('th[data-col]').forEach(function(th){th.classList.remove('sorted-asc','sorted-desc');});var th=document.querySelector('th[data-col='+sortCol+']');if(th){th.classList.add(sortAsc?'sorted-asc':'sorted-desc');}}function sortBy(col){if(sortCol===col){sortAsc=!sortAsc;"

if old in c:
    c = c.replace(old, new)
    print('updateArrows added')
else:
    print('ERROR: sortBy pattern not found')

# Add fmtMktcap to JS
old2 = "function scoreColor(s){return s>=80?"
new2 = "function fmtMktcap(v){if(v>=1000)return'$'+Math.round(v/1000*100)/100+'T';if(v>=1)return'$'+Math.round(v*100)/100+'B';return'$'+Math.round(v*1000)+'M';}function scoreColor(s){return s>=80?"

if new2 not in c:
    if old2 in c:
        c = c.replace(old2, new2)
        print('fmtMktcap added')
    else:
        print('ERROR: scoreColor pattern not found')
else:
    print('fmtMktcap already in code')

# Also add call to updateArrows after sortBy sorts
old3 = "});updateArrows();renderTable();"
new3 = "});updateArrows();renderTable();}"
if old3 in c:
    c = c.replace(old3, new3)
    print('updateArrows call updated')
else:
    print('updateArrows call pattern:', repr(c[c.find('renderTable()')-20:c.find('renderTable()')+30]))

with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')