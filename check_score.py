content = open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html').read()
idx = content.find("color:'+c+'")
if idx >= 0:
    print(content[idx-10:idx+80])
else:
    print('NOT found')
    # check for the score cell in table rows
    idx = content.find('r.score')
    print('r.score at:', idx)
    if idx >= 0:
        print(content[idx-20:idx+60])