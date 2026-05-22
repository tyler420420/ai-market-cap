with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

s_short = c.count('SHORT')
s_squeeze = c.count('SQUEEZE')
print(f'SHORT: {s_short}, SQUEEZE: {s_squeeze}')

idx = c.find('function renderTable()')
if idx >= 0:
    snippet = c[idx:idx+3000]
    short_rt = snippet.count('SHORT')
    squeeze_rt = snippet.count('SQUEEZE')
    print(f'SHORT in renderTable: {short_rt}')
    print(f'SQUEEZE in renderTable: {squeeze_rt}')
    if short_rt == 0 and squeeze_rt > 0:
        print('renderTable still has SQUEEZE!')
        # Show the squeeze line
        i = snippet.find('SQUEEZE')
        print(repr(snippet[i-30:i+80]))