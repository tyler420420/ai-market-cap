import requests, secrets, time

token = secrets.token_hex(32)
expires = int(time.time()) + 86400
s = requests.Session()
s.cookies.set('scanner_session', f'{token}|{expires}')
r = s.get('https://aismarketcap.com/scanner', timeout=15)
print('Status:', r.status_code)
print('Has Chat button:', 'Chat' in r.text and 'chat-btn' in r.text)
print('Has new toggleChat (p.style.display):', 'p.style.display' in r.text)
print('Has new sendMsg:', 'var i=document.getElementById' in r.text)
print('Total &amp;:', r.text.count('&amp;'))
print()
# Show what's around the chat button
import re
m = re.search(r'id="chat-btn"[^>]*>', r.text)
if m:
    print('Chat button HTML:', r.text[m.start():m.start()+100])