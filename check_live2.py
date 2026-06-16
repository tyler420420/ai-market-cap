import requests
r = requests.get('https://aismarketcap.com', timeout=15)
c = r.text
dram = 'TRENDING ETF' in c
ipos = c.count('TOP IPO')
print(f"DRAM card: {dram}")
print(f"IPO cards: {ipos}")
# Check if it has the new code
print(f"Has DRAM link: {'DRAM' in c}")
print(f"Has margin-left: {'margin-left:24px' in c}")