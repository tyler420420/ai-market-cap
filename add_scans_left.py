# Add scans remaining display and limit handling to the desktop HTML

content = open('ai_earnings_today.html', encoding='utf-8').read()

# 1. Add scans remaining to the button area
old_btn = '<button class=btn id=scanBtn onclick=runScan()>Run Scan</button>'
new_btn = '<button class=btn id=scanBtn onclick=runScan()>Run Scan</button><span id=scansLeft style="font-size:0.75em;color:#8b949e;margin-left:6px"></span>'
if old_btn in content:
    content = content.replace(old_btn, new_btn)
    print('Step1: Added scansLeft span')
else:
    print('Step1: NOT found')

# 2. Add fetch('/api/scans') call and limit handling in runScan
old_runscan = """function runScan(){scanBtn.disabled=true;warnMsg.textContent='Starting scan...';var x=new XMLHttpRequest();x.open('POST','/run',true);x.onload=function(){if(x.responseURL&&x.responseURL.endsWith('/pricing')){window.location.href='/pricing';return;}warnMsg.textContent='Scan started! Reloading...';location.reload(true);};x.onerror=function(){scanBtn.disabled=false;warnMsg.textContent='Error - try again.';setTimeout(function(){warnMsg.style.display='none';},4000);};x.send();}"""
new_runscan = """function runScan(){scanBtn.disabled=true;warnMsg.textContent='Starting scan...';var x=new XMLHttpRequest();x.open('POST','/run',true);x.onload=function(){if(x.responseURL&&x.responseURL.endsWith('/pricing')){window.location.href='/pricing';return;}if(x.status===429){scanBtn.disabled=false;warnMsg.textContent='Daily scan limit reached (2/day). Next scan available tomorrow.';warnMsg.style.display='block';setTimeout(function(){warnMsg.style.display='none';},6000);return;}warnMsg.textContent='Scan started! Reloading...';location.reload(true);};x.onerror=function(){scanBtn.disabled=false;warnMsg.textContent='Error - try again.';setTimeout(function(){warnMsg.style.display='none';},4000);};x.send();}function updateScansLeft(){fetch('/api/scans').then(function(r){return r.json();}).then(function(d){var el=document.getElementById('scansLeft');if(el){el.textContent='('+d.remaining+'/'+d.limit+' scans today)';}}).catch(function(){});}updateScansLeft();"""
if old_runscan in content:
    content = content.replace(old_runscan, new_runscan)
    print('Step2: Updated runScan')
else:
    print('Step2: NOT found')

with open('ai_earnings_today.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')