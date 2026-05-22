with open('ai_earnings_tight.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Super bright neon green gradient
c = c.replace('style="background:linear-gradient(135deg,#0d2b1a,#162016);border:1px solid #2ea043;border-radius:8px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px"',
              'style="background:linear-gradient(135deg,#003d0e,#00a33c);border:2px solid #00ff55;border-radius:16px;padding:28px 32px;display:flex;align-items:center;gap:18px;flex-wrap:wrap;margin:12px 0;animation:feat-glow 2s ease-in-out infinite"')

open('ai_earnings_tight.html', 'w', encoding='utf-8').write(c)
print('Done')