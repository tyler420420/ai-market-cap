with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find buy and hold in static rows
idx = c.find("'+r.buy+'")
print('Buy context:', repr(c[idx-30:idx+30]))
idx2 = c.find("'+r.hold+'")
print('Hold context:', repr(c[idx2-30:idx2+30]))
# Also check JS version
idx3 = c.find("html+='<td>'+r.buy+'<")
print('JS Buy:', repr(c[idx3:idx3+50]))