f=open('scanner_web.py','r',encoding='utf-8')
c=f.read()
f.close()
idx=c.find('@app.route("/cron")')
if idx>0:
    print(c[idx:idx+600])
else:
    print('no /cron route')
    print('cron mentions:', c.count('cron'))
    # check if there's an auto-scan loop
    idx=c.find('threading.Thread')
    print('threading.Thread:', idx)
    if idx>0:
        print(c[idx:idx+400])