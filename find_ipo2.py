import re
c = open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8').read()

# Find the IPO section with context
idx = c.find('SOONEST TOP IPO')
if idx >= 0:
    # Go back to find the container
    start = c.rfind('<div', 0, idx)
    print("Start:", start)
    print(c[start:idx+800])
else:
    print("SOONEST not found")