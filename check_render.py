with open('ai_earnings_57day_20260519_2256.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find renderTable and show the exact function
start = c.find('function renderTable')
# Find the next function or DOMContentLoaded
end = c.find('document.addEventListener', start)
print(repr(c[start:end]))
print()
# Check: is 'var html' declared inside renderTable?
inner = c[start:end]
print('has var html:', 'var html' in inner)
print('has innerHTML:', 'innerHTML' in inner)