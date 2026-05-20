import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scanner_web.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find the /scanner and / routes
for kw in ['@app.route("/")', '@app.route("/scanner")', 'def index', 'def scanner']:
    idx = content.find(kw)
    if idx >= 0:
        print(kw)
        print(content[idx:idx+300])
        print('---')