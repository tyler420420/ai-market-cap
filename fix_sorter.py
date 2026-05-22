with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find and replace the sortBy + updateArrows section
old = "html += \"var sortCol='days_left';var sortAsc=true;function getVal(r,col){var m={'ticker':r.ticker,'company_name':r.company_name,'score':r.score,'earnings_date':r.earnings_date,'days_left':r.days_left,'price':r.price,'pe_target':r.pe_target,'3d':r['3d'],'5d':r['5d'],'analysts':r.analysts,'sb':r.sb,'buy':r.buy,'hold':r.hold,'sell':r.sell,'mktcap':r.mktcap'};return m[col]||r[col]||0;}function updateArrows(){document.querySelectorAll('th[data-col]').forEach(function(th){th.classList.remove('sorted-asc','sorted-desc');});var th=document.querySelector('th[data-col=\"'+sortCol+'\"]');if(th){th.classList.add(sortAsc?'sorted-asc':'sorted-desc');}}function sortBy(col){if(sortCol===col){sortAsc=!sortAsc;}else{sortCol=col;sortAsc=col==='days_left'||col==='score'||col==='analysts'||col==='sb'||col==='buy'||col==='hold'||col==='sell'||col==='price'||col==='pe_target'||col==='3d'||col==='5d'||col==='mktcap';}var dirs={'ticker':1,'company_name':1};var asc=dirs[col]?sortAsc:!sortAsc;rowsData.sort(function(a,b){var va=getVal(a,col),vb=getVal(b,col);if(typeof va==='number')return asc?va-vb:vb-va;return asc?String(va).localeCompare(String(vb)):String(vb).localeCompare(String(va));});renderTable();updateArrows();}"

new = "html += \"var sortCol='days_left';var sortAsc=true;window.sortBy=function(col){if(sortCol===col){sortAsc=!sortAsc;}else{sortCol=col;sortAsc=col==='days_left'||col==='score'||col==='analysts'||col==='sb'||col==='buy'||col==='hold'||col==='sell'||col==='price'||col==='pe_target'||col==='3d'||col==='5d'||col==='mktcap';}var dirs={'ticker':1,'company_name':1};var asc=dirs[col]?sortAsc:!sortAsc;rowsData.sort(function(a,b){var va=getVal(a,col),vb=getVal(b,col);if(typeof va==='number')return asc?va-vb:vb-va;return asc?String(va).localeCompare(String(vb)):String(vb).localeCompare(String(va));});renderTable();document.querySelectorAll('th[data-col]').forEach(function(th){th.style.color='#8b949e';th.classList.remove('sorted-asc','sorted-desc');});var th=document.querySelector('th[data-col=\"'+sortCol+'\"]');if(th){th.classList.add(sortAsc?'sorted-asc':'sorted-desc');th.style.color='#00ff88';}};function getVal(r,col){var m={'ticker':r.ticker,'company_name':r.company_name,'score':r.score,'earnings_date':r.earnings_date,'days_left':r.days_left,'price':r.price,'pe_target':r.pe_target,'3d':r['3d'],'5d':r['5d'],'analysts':r.analysts,'sb':r.sb,'buy':r.buy,'hold':r.hold,'sell':r.sell,'mktcap':r.mktcap'};return m[col]||r[col]||0;}function updateArrows(){document.querySelectorAll('th[data-col]').forEach(function(th){th.classList.remove('sorted-asc','sorted-desc');});var th=document.querySelector('th[data-col=\"'+sortCol+'\"]');if(th){th.classList.add(sortAsc?'sorted-asc':'sorted-desc');}}\";html += \""

if old in c:
    c = c.replace(old, new)
    with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Fixed!')
else:
    print('OLD NOT FOUND')
    with open('old_check.txt', 'w', encoding='utf-8') as f:
        f.write(old)
    # Try to find partial match
    idx = c.find("var sortCol='days_left'")
    print('sortCol found at:', idx)
    print('First 200 chars:', repr(c[idx:idx+200]))