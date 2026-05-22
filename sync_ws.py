with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_tight.html', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('data-col="pe_target">PE Target</th>', 'data-col="pe_target">Post Earnings<br>Target</th>')
with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_tight.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')