pricing_html = """<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pricing - AI Market Cap</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: Segoe UI, Arial, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; }
.header { background: linear-gradient(135deg,#1a1f2e,#161b22); padding: 20px 30px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
.header h1 { color: #58a6ff; font-size: 1.5em; }
.header a { color: #58a6ff; text-decoration: none; font-size: 0.9em; }
.container { max-width: 900px; margin: 0 auto; padding: 60px 20px; text-align: center; }
h2 { color: #fff; font-size: 2em; margin-bottom: 10px; }
.subtitle { color: #8b949e; font-size: 1.1em; margin-bottom: 50px; }
.plans { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
.plan { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 30px; width: 260px; text-align: left; }
.plan h3 { color: #fff; font-size: 1.2em; margin-bottom: 10px; }
.plan .price { font-size: 2.5em; font-weight: bold; color: #fff; margin-bottom: 5px; }
.plan .price span { font-size: 0.4em; color: #8b949e; font-weight: normal; }
.plan .period { color: #8b949e; font-size: 0.85em; margin-bottom: 25px; }
.plan ul { list-style: none; margin-bottom: 25px; }
.plan li { color: #c9d1d9; font-size: 0.88em; padding: 6px 0; }
.plan li::before { content: "✓ "; color: #2ea043; }
.plan li.off::before { content: "✗ "; color: #ff6b6b; }
.plan li.off { color: #6e7681; }
.plan .cta { display: block; background: #238636; color: #fff; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 0.95em; }
.plan .cta:hover { background: #2ea043; }
.plan.featured { border-color: #ffd700; box-shadow: 0 0 20px rgba(255,215,0,0.2); }
.plan.featured .cta { background: #238636; }
.plan.featured .cta:hover { background: #2ea043; }
.back-link { display: inline-block; margin-top: 40px; color: #58a6ff; text-decoration: none; font-size: 0.9em; }
.back-link:hover { color: #79b8ff; }
</style></head><body>
<div class=header>
    <h1><a href="/" style="color:#58a6ff;text-decoration:none">AI Market Cap</a></h1>
    <a href="/">View Scanner</a>
</div>
<div style="background:#1a2a1a;border:1px solid #2ea043;border-radius:8px;padding:12px 18px;margin:30px auto;max-width:880px;text-align:center;font-size:0.9em;color:#2ea043">Full scan runs once daily for free at 6:30 AM PT — auto-updated every market day</div>
<div class=container>
    <h2>Subscribe to run additional scans<br>and use the AI chat assistant.</h2>
    <p class=subtitle>Unlock full access to the scanner</p>
    <div class=plans>
        <div class=plan>
            <h3>Monthly</h3>
            <div class=price>$149<span>/mo</span></div>
            <div class=period>Billed monthly</div>
            <ul>
                <li>2 additional scans per day</li>
                <li>AI Chat Assistant</li>
                <li>Score + PE/3D/5D targets</li>
                <li>AI Suggested Trade</li>
                <li>Live price ticker</li>
                <li>News per stock</li>
            </ul>
            <a href="/create-checkout?plan=monthly" class=cta>Subscribe - $149/mo</a>
        </div>
        <div class="plan featured">
            <h3>Annual</h3>
            <div class=price>$999<span>/yr</span></div>
            <div class=period>Save $789 vs monthly</div>
            <ul>
                <li>Everything in Monthly</li>
                <li>Save $789/year</li>
            </ul>
            <a href="/create-checkout?plan=annual" class=cta>Subscribe - $999/yr</a>
        </div>
    </div>
</div>
</body></html>"""

with open(r'C:\Users\Tyler_AI\Desktop\pricing.html', 'w', encoding='utf-8') as f:
    f.write(pricing_html)
print('Saved')