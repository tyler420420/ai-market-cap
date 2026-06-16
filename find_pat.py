path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all occurrences of the ticker pattern
pattern = "html+='<tr style=\"background:'+bg+'\"><td><strong><a href=\"https://finance.yahoo.com/quote/'+r.ticker+'\" target=\"_blank\" style=\"color:#66b2ff\">'+r.ticker+'</a></strong></td>"
count = content.count(pattern)
print(f'Pattern occurrences: {count}')

# Find where the pattern starts
idx = content.find(pattern)
print(f'First occurrence at: {idx}')

# Check if there's another occurrence in the sortCol line
idx2 = content.find("var sortCol")
if idx2 >= 0:
    # Is the pattern before or after?
    if idx < idx2:
        print(f'Pattern is at {idx}, sortCol is at {idx2} - pattern comes first')
    else:
        print(f'Pattern is at {idx}, sortCol is at {idx2} - pattern comes after')

# Also check for the actual changed text
new_pattern = 'html+=\'<tr style=\\"background:\'+bg+\'\\"><td data-label="Ticker"><strong><a href=\\"https://finance.yahoo.com/quote/\\'+r.ticker+\'\\" target=\\"_blank\\" style=\\"color:#66b2ff\\">\\'+r.ticker+\'</a></strong></td>'
count2 = content.count(new_pattern)
print(f'New pattern occurrences: {count2}')