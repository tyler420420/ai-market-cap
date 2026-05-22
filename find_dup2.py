c = open('ai_earnings_today.html', encoding='utf-8').read()

# Find first "Strong Buy" occurrence
idx1 = c.find('Strong Buy')
# Find second "Strong Buy" occurrence  
idx2 = c.find('Strong Buy', idx1 + 1)

print(f'First Strong Buy at: {idx1}')
print(f'Second Strong Buy at: {idx2}')
print(f'\nFirst occurrence context:')
print(c[idx1-100:idx1+100])
print(f'\nSecond occurrence context:')
print(c[idx2-100:idx2+100])