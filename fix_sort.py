with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

old = "tbody.innerHTML=html;}\n    html += '</script>'"
new = "tbody.innerHTML=html;document.querySelectorAll('th[data-col]').forEach(function(th){th.style.cursor='pointer';th.title='Click to sort';});updateArrows();}\n    html += '</script>'"

if old in c:
    c = c.replace(old, new)
    print('Replacement 1 done')
else:
    print('ERROR: could not find old string 1')
    print(repr(c[c.find('tbody.innerHTML=html'):c.find('html += </script>')]))

# Also replace mktcap in JS
old2 = "html+='<td>'+r.mktcap+'</td>'"
new2 = "html+='<td>'+fmtMktcap(r.mktcap)+'</td>'"
if old2 in c:
    c = c.replace(old2, new2)
    print('Replacement 2 done')
else:
    print('ERROR: could not find mktcap in JS')

with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')