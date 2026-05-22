c = open('ai_earnings_today.html', encoding='utf-8').read()

# Find all counter sections and see where they lead
idx1 = c.find('Strong Buy')
# Find context after first counter - should go to IPO boxes
print('AFTER first Strong Buy (200 chars):')
print(repr(c[idx1+50:idx1+250]))

# Find second counter
idx2 = c.find('Strong Buy', idx1 + 1)
print('\n---\nAFTER second Strong Buy (200 chars):')
print(repr(c[idx2+50:idx2+250]))