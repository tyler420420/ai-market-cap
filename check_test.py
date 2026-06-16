c = open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8').read()

# Check IPO count
ipos = c.count('TOP IPO')
dram = 'DRAM' in c and 'Top ETF' in c
dram_price = c[c.find('Top ETF'):c.find('Top ETF')+200] if 'Top ETF' in c else 'NOT FOUND'

print(f"IPO cards: {ipos}")
print(f"DRAM card present: {dram}")
print(f"DRAM section: {dram_price[:200]}")
print()
# Count IPO divs
idx = c.find('SOONEST TOP IPO')
end = c.find('Top ETF')
print("IPO section:")
print(c[idx:end])