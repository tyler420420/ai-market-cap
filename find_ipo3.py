import re
c = open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8').read()

# Find the full IPO strip
idx = c.find('SOONEST TOP IPO')
# Find the container before it
start = c.rfind('<div ', 0, idx)
# Find end - look for the closing div of the container
# The container likely ends before the ticker strip or table
end = c.find('ticker-strip', start)
if end < 0:
    end = c.find('stockTable', start)
print("Container start:", start)
print("Container end:", end)
print()
print("FULL IPO SECTION:")
print(c[start:end])
print()
print("Length:", end - start)