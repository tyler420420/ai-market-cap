c = open('ai_earnings_today.html', encoding='utf-8').read()

idx1 = c.find('Strong Buy')
idx2 = c.find('Strong Buy', idx1 + 1)

# Get more context before each
print('BEFORE first Strong Buy (200 chars):')
print(repr(c[idx1-200:idx1]))
print('\n---\n')
print('BEFORE second Strong Buy (200 chars):')
print(repr(c[idx2-200:idx2]))