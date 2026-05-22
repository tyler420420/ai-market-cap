# Update pricing page - clear value prop

content = open('scanner_web.py', encoding='utf-8').read()

old_subtitle = """<p class=subtitle>2 scans per day, real-time prices, and AI-powered trade picks.</p>"""
new_subtitle = """<p class=subtitle>The scanner auto-runs free every market day at 6:30 AM PT. Subscribe to run additional scans and use the AI chat assistant.</p>"""
if old_subtitle in content:
    content = content.replace(old_subtitle, new_subtitle)
    print('1. Updated subtitle')
else:
    print('1. Not found:', repr(old_subtitle[:80]))

old_monthly = """<ul>
                <li>2 scans per day</li>
                <li>Score + PE/3D/5D targets</li>
                <li>AI Suggested Trade</li>
                <li>Live price ticker</li>
                <li>News per stock</li>
                <li>Auto-scan at 6:30 AM PT daily</li>
            </ul>
            <a href="/create-checkout?plan=monthly" class=cta>Subscribe - $149/mo</a>
        </div>
        <div class="plan featured">
            <h3>Annual</h3>
            <div class=price>$999<span>/yr</span></div>
            <div class=period>Save $789 vs monthly</div>
            <ul>
                <li>2 scans per day</li>
                <li>Score + PE/3D/5D targets</li>
                <li>AI Suggested Trade</li>
                <li>Live price ticker</li>
                <li>News per stock</li>
                <li>Auto-scan at 6:30 AM PT daily</li>
            </ul>"""
new_monthly = """<ul>
                <li>2 additional scans per day</li>
                <li>AI Chat Assistant</li>
                <li>Score + PE/3D/5D targets</li>
                <li>AI Suggested Trade</li>
                <li>Live price ticker</li>
                <li>News per stock</li>
                <li>Auto-scan at 6:30 AM PT daily</li>
            </ul>
            <a href="/create-checkout?plan=monthly" class=cta>Subscribe - $149/mo</a>
        </div>
        <div class="plan featured">
            <h3>Annual</h3>
            <div class=price>$999<span>/yr</span></div>
            <div class=period>Save $789 vs monthly</div>
            <ul>
                <li>2 additional scans per day</li>
                <li>AI Chat Assistant</li>
                <li>Score + PE/3D/5D targets</li>
                <li>AI Suggested Trade</li>
                <li>Live price ticker</li>
                <li>News per stock</li>
                <li>Auto-scan at 6:30 AM PT daily</li>
            </ul>"""
if old_monthly in content:
    content = content.replace(old_monthly, new_monthly)
    print('2. Updated monthly/annual lists')
else:
    print('2. Not found')

with open('scanner_web.py', 'w', encoding='utf-8') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax Error at line {e.lineno}: {e.msg}')