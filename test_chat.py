import requests, secrets, time, re

# Simulate login
s = requests.Session()
r = s.post('http://127.0.0.1:18766/login', data={'password': 'trading2026'}, allow_redirects=False)
print('Login status:', r.status_code)
print('Has session cookie:', 'scanner_session' in s.cookies)

# Get scanner page
r2 = s.get('http://127.0.0.1:18766/scanner')
print('Scanner status:', r2.status_code)
print('Scanner size:', len(r2.text))
print('Has chat-btn:', 'chat-btn' in r2.text)
print()

# Check the chat HTML elements exist
btn = re.search(r'id="chat-btn"', r2.text)
panel = re.search(r'id="chat-panel"', r2.text)
css = re.search(r'#chat-', r2.text)
print('chat-btn element found:', bool(btn))
print('chat-panel element found:', bool(panel))
print('chat CSS found:', bool(css))

# Print toggleChat function
toggle_match = re.search(r'function toggleChat', r2.text)
print('toggleChat function found:', bool(toggle_match))

# Check if body has onload or other blocking
body_end = r2.text.rfind('</body>')
snippet = r2.text[max(0,body_end-500):body_end]
print()
print('--- LAST 500 CHARS BEFORE </body> ---')
print(snippet)