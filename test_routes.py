import requests

# Test routes
r = requests.get('http://localhost:18766/', timeout=5)
print('Home (/) status:', r.status_code)

r2 = requests.get('http://localhost:18766/pricing', timeout=5)
print('/pricing status:', r2.status_code)

r3 = requests.post('http://localhost:18766/run', timeout=5)
print('/run (POST) status:', r3.status_code, '| location:', r3.headers.get('Location', 'none'))

# Check pricing content
print('\nPricing page content preview:')
print(r2.text[:500])