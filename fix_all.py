import sys
sys.stdout.reconfigure(encoding='utf-8')

# Fix scanner_web.py: scan_latest sort by mtime
with open('scanner_web.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Fix scan_latest to sort by mtime
old = 'html_files = sorted(workspace.glob("ai_earnings_57day_*.html"), reverse=True)'
new = 'html_files = sorted(workspace.glob("ai_earnings_57day_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)'
if old in content:
    content = content.replace(old, new)
    print('Fixed scan_latest sort')
else:
    print('Already fixed or pattern changed')

with open('scanner_web.py', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

# Fix ai_earnings_web.html: reload to /scan/latest
with open('ai_earnings_web.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

old_reload = "setTimeout(function(){clearDoneMsg();location.reload(true);},3000);"
new_reload = "setTimeout(function(){clearDoneMsg();window.location='/scan/latest?_='+Date.now();},3000);"
if old_reload in content:
    content = content.replace(old_reload, new_reload)
    with open('ai_earnings_web.html', 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print('Fixed HTML reload to /scan/latest')
else:
    print('Reload already fixed')

# Verify syntax
import ast
ast.parse(open('scanner_web.py', 'r', encoding='utf-8', errors='replace').read())
print('scanner_web.py syntax: OK')