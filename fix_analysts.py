with open('ai_earnings_scanner.py', 'r') as f:
    lines = f.readlines()

line538 = lines[537]

# The problem: after fixing analysts, there's a double semicolon
# "html+='<td style="color:#bf8fff">'+r.analysts+'</td>';';"
# Should be: "html+='<td style="color:#bf8fff">'+r.analysts+'</td>';"

bad = "html+='<td style=\"color:#bf8fff\">'+r.analysts+'</td>';';"
good = "html+='<td style=\"color:#bf8fff\">'+r.analysts+'</td>';"

if bad in line538:
    lines[537] = line538.replace(bad, good)
    with open('ai_earnings_scanner.py', 'w') as f:
        f.writelines(lines)
    print('Fixed double semicolon!')
else:
    print('Pattern not found, checking...')
    idx = line538.find('color:#bf8fff')
    if idx >= 0:
        print(repr(line538[idx:idx+80]))