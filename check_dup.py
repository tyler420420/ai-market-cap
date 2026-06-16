path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Count html+='<td patterns
count = content.count("html+='<td>")
print(f'html+="<td>" count: {count}')
# Check if there are any in the sortCol function
idx = content.find('var sortCol')
seg = content[idx:idx+200]
print('sortCol section:')
print(repr(seg[:100]))
# Check how many html+= statements exist
import re
html_plus = re.findall(r"html\+='<td>", content)
print(f'\nhtml+="<td>" occurrences: {len(html_plus)}')