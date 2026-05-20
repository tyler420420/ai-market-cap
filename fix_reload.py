import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('ai_earnings_web.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

old_reload = "setTimeout(function(){clearDoneMsg();location.reload(true);},3000);"
new_reload = "setTimeout(function(){clearDoneMsg();window.location='scan/latest?_='+Date.now();},3000);"

if old_reload in content:
    content = content.replace(old_reload, new_reload)
    with open('ai_earnings_web.html', 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print('Fixed reload to use /scan/latest')
else:
    print('Old reload pattern not found. Searching...')
    idx = content.find('location.reload')
    print(content[max(0,idx-50):idx+100])