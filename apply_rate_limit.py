# Minimal edits to scanner_web.py - add 2/day scan limit + update pricing

content = open('scanner_web.py', encoding='utf-8').read()

# 1. Add scan counts file + helpers
old_subs = """SUBS_FILE = Path(__file__).parent / "subscriptions.json\""""
new_subs = """SUBS_FILE = Path(__file__).parent / "subscriptions.json\"
SCAN_COUNTS_FILE = Path(__file__).parent / "scan_counts.json\"
MAX_SCANS_PER_DAY = 2"""
if old_subs in content:
    content = content.replace(old_subs, new_subs)
    print('1. Added files')
else:
    print('1. Already present')

# 2. Add helper functions after get_subscriptions
old_getsubs = """def get_subscriptions():
    if SUBS_FILE.exists():
        try:
            return json.loads(SUBS_FILE.read_text())
        except:
            return {}
    return {}"""
new_getsubs = """def get_subscriptions():
    if SUBS_FILE.exists():
        try:
            return json.loads(SUBS_FILE.read_text())
        except:
            return {}
    return {}

def get_scan_counts():
    if SCAN_COUNTS_FILE.exists():
        try:
            return json.loads(SCAN_COUNTS_FILE.read_text())
        except:
            return {}
    return {}

def get_scans_today(customer_id):
    counts = get_scan_counts()
    today = datetime.now(PT).strftime(\"%Y-%m-%d\")
    key = f\"{customer_id}:{today}\"
    return counts.get(key, 0)

def increment_scan_count(customer_id):
    counts = get_scan_counts()
    today = datetime.now(PT).strftime(\"%Y-%m-%d\")
    key = f\"{customer_id}:{today}\"
    counts[key] = counts.get(key, 0) + 1
    save_scan_counts(counts)

def save_scan_counts(counts):
    # clean up old dates
    today = datetime.now(PT).strftime(\"%Y-%m-%d\")
    counts = {k: v for k, v in counts.items() if k.split(\":\")[0] == today}
    SCAN_COUNTS_FILE.write_text(json.dumps(counts))"""
if old_getsubs in content:
    content = content.replace(old_getsubs, new_getsubs)
    print('2. Added helpers')
else:
    print('2. Already present')

# 3. Add /api/scans endpoint before /webhook
old_webhook = """@app.route(\"/webhook\", methods=[\"POST\"])
def webhook():"""
new_webhook = """@app.route(\"/api/scans\", methods=[\"GET\"])
def api_scans():
    customer_id = request.cookies.get(\"stripe_customer\", \"\")
    token = request.cookies.get(COOKIE_NAME, \"\")
    used = get_scans_today(customer_id) if customer_id else get_scans_today(token)
    return jsonify({'used': used, 'limit': MAX_SCANS_PER_DAY, 'remaining': max(0, MAX_SCANS_PER_DAY - used)})

@app.route(\"/webhook\", methods=[\"POST\"])
def webhook():"""
if old_webhook in content:
    content = content.replace(old_webhook, new_webhook)
    print('3. Added /api/scans')
else:
    print('3. Already present')

# 4. Update /run endpoint to check limit
old_run = """@app.route(\"/run\", methods=[\"POST\"])
def api_run():
    \"\"\"Run scan - requires active subscription\"\"\"
    token = request.cookies.get(COOKIE_NAME, \"\")
    customer_id = request.cookies.get(\"stripe_customer\", \"\")

    # Check subscription
    subs = get_subscriptions()
    is_active = subs.get(customer_id, {}).get('status') == 'active' or subs.get(token, {}).get('status') == 'active'

    if not is_active:
        return redirect(\"/pricing\")

    trigger_scan()
    return \"ok\""""
new_run = """@app.route(\"/run\", methods=[\"POST\"])
def api_run():
    \"\"\"\"Run scan - requires active subscription + max 2/day\"\"\"
    token = request.cookies.get(COOKIE_NAME, \"\")
    customer_id = request.cookies.get(\"stripe_customer\", \"\")

    # Check subscription
    subs = get_subscriptions()
    is_active = subs.get(customer_id, {}).get('status') == 'active' or subs.get(token, {}).get('status') == 'active'

    if not is_active:
        return redirect(\"/pricing\")

    # Check scan limit
    key_id = customer_id if customer_id else token
    if get_scans_today(key_id) >= MAX_SCANS_PER_DAY:
        return jsonify({'error': 'limit_reached', 'message': f'Daily scan limit reached ({MAX_SCANS_PER_DAY}/day). Try again tomorrow.'}), 429

    trigger_scan()
    increment_scan_count(key_id)
    return \"ok\""""
if old_run in content:
    content = content.replace(old_run, new_run)
    print('4. Updated /run')
else:
    print('4. Already present')

with open('scanner_web.py', 'w', encoding='utf-8') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax Error at line {e.lineno}: {e.msg}')