f=open('scanner_web.py','r',encoding='utf-8')
c=f.read()
f.close()

# Add /cron route before the WEB ROUTES section
old = '# ===== WEB ROUTES ====='
new = '''# ===== AUTO SCAN CRON =====

@app.route("/cron")
def cron():
    """Triggered by Railway cron job at 6:30 AM PT daily"""
    now = datetime.now(PT)
    today = now.date()
    if getattr(cron, 'last_run', None) == today:
        return "Already ran today", 200
    cron.last_run = today
    # Run scan in background thread
    def do_scan():
        try:
            subprocess.run(
                [sys.executable, str(Path(__file__).parent / "ai_earnings_scanner.py")],
                capture_output=True, text=True,
                encoding='utf-8', errors='replace', timeout=180,
                cwd=str(Path(__file__).parent)
            )
        except Exception as e:
            print("[Cron] Scan error:", e)
    threading.Thread(target=do_scan, daemon=True).start()
    return "Scan triggered", 200

# ===== WEB ROUTES ====='''

c = c.replace(old, new)

f=open('scanner_web.py','w',encoding='utf-8')
f.write(c)
f.close()
print('done')