c = open('ai_earnings_scanner.py', encoding='utf-8').read()
old = "html += '*{margin:0;padding:0;box-sizing:border-box}body{font-family:Segoe UI,Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:20px}'"
new = "html += '*{margin:0;padding:0;box-sizing:border-box}body{font-family:Segoe UI,Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:0;margin:0}'"
if old in c:
    c = c.replace(old, new)
    open('ai_earnings_scanner.py', 'w', encoding='utf-8').write(c)
    print('Source updated')
else:
    print('NOT found')