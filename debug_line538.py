with open('ai_earnings_scanner.py') as f:
    lines = f.readlines()
line538 = lines[537]
idx = line538.find("'mktcap'")
print('mktcap at:', idx)
if idx > 0:
    print('Context:', repr(line538[idx-5:idx+30]))