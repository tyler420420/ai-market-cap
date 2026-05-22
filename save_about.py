about_html = """<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/png" href="/static/logo.png">
<title>How It Works - AI Market Cap</title>
<meta name="description" content="Learn how AI Market Cap's pre-earnings momentum scanner works. Scoring methodology, PE targets, 3-day and 5-day implied moves explained.">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: Segoe UI, Arial, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; }
.header { background: linear-gradient(135deg,#1a1f2e,#161b22); padding: 20px 30px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
.header h1 a { color: #58a6ff; font-size: 1.5em; text-decoration: none; }
.header a.nav-link { color: #58a6ff; text-decoration: none; font-size: 0.9em; }
.container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
h2 { color: #fff; font-size: 1.8em; margin: 35px 0 15px; border-bottom: 1px solid #30363d; padding-bottom: 10px; }
h2:first-child { margin-top: 0; }
h3 { color: #2ea043; font-size: 1.15em; margin: 20px 0 8px; }
p { color: #c9d1d9; font-size: 0.95em; line-height: 1.7; margin-bottom: 14px; }
ul { margin: 0 0 14px 20px; }
li { color: #c9d1d9; font-size: 0.95em; line-height: 1.7; margin-bottom: 6px; }
.faq-q { color: #ffd700; font-weight: bold; margin-bottom: 6px; }
.disclaimer { margin-top: 40px; padding: 16px 20px; background: #1a1a1a; border-radius: 8px; border: 1px solid #c0392b; color: #999; font-size: 0.8em; line-height: 1.6; }
.highlight { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin: 15px 0; }
.highlight strong { color: #2ea043; }
.toc { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px 25px; margin-bottom: 30px; }
.toc a { color: #58a6ff; text-decoration: none; display: block; padding: 4px 0; }
.toc a:hover { color: #79b8ff; }
</style></head><body>
<div class=header>
    <h1><a href="/">AI Market Cap</a></h1>
    <a href="/pricing" class=nav-link>Subscribe</a>
</div>
<div class=container>
    <div class=toc>
        <a href="#methodology">Scoring Methodology</a>
        <a href="#targets">PE / 3D / 5D Targets</a>
        <a href="#ai">AI Suggested Trade</a>
        <a href="#faq">FAQ</a>
    </div>

    <h2 id=methodology>Scoring Methodology</h2>
    <p>Every stock is scored 0-100 based on four factors:</p>
    <div class=highlight>
        <strong>Analyst Ratings (30 pts)</strong> - Percentage of Buy + Strong Buy ratings across all covering analysts. More bullish analysts = higher score.<br><br>
        <strong>Buy Percentage (30 pts)</strong> - Raw % of analysts with Buy or Strong Buy. We weight this separately to capture conviction level.<br><br>
        <strong>5-Day Upside (20 pts)</strong> - ATM straddle x 5, expressed as % of current stock price. Higher implied move potential = higher score.<br><br>
        <strong>Strong Buy Count (2 pts each, max 20)</strong> - Each Strong Buy rating adds 2 points. Stocks with 10+ Strong Buy ratings get the full 20 pts.
    </div>
    <p>Stocks scoring <strong style="color:#00ff88">80+</strong> are flagged Strong Buy. Stocks scoring <strong style="color:#58a6ff">65-79</strong> are Watch.</p>

    <h2 id=targets>PE / 3-Day / 5-Day Target Columns</h2>
    <h3>PE Target</h3>
    <p>Estimated exit price using an ATM straddle at <strong>1x implied move</strong>. This is the conservative estimate - assumes the stock moves exactly what the options market expects, in the direction of the trend.</p>
    <h3>3-Day Target</h3>
    <p>Estimated exit price using an ATM straddle at <strong>3x implied move</strong>. Mid-range scenario for stocks 3-7 days from earnings.</p>
    <h3>5-Day Target</h3>
    <p>Estimated exit price using an ATM straddle at <strong>5x implied move</strong>. Maximum upside scenario - appropriate for stocks 5+ days out or high-IV names where the straddle is expensive.</p>
    <h3>What is a Straddle?</h3>
    <p>An ATM straddle buys both a call and a put at the same strike. Its value changes based on how much the stock moves, regardless of direction. We use the straddle price to back-calculate what stock move is being priced in by the market.</p>

    <h2 id=ai>AI Suggested Trade</h2>
    <p>The banner at the top highlights the single best trade opportunity - the stock closest to earnings with the highest composite score. It factors in score weight, proximity to earnings, and analyst conviction.</p>
    <p>This is not financial advice. It's one trader's observation of where the math and momentum align.</p>

    <h2 id=faq>Frequently Asked Questions</h2>
    <p class=faq-q>Is this a financial advisor service?</p>
    <p>No. AI Market Cap is a data tool for informational purposes only. We are not licensed financial advisors. Always do your own research.</p>
    <p class=faq-q>How often does the scanner update?</p>
    <p>The free scan runs automatically every market day at 6:30 AM PT. Subscribers can run up to 2 additional scans per day on demand.</p>
    <p class=faq-q>What data sources are used?</p>
    <p>Stock prices and option data come from Yahoo Finance. Analyst ratings are pulled from Yahoo Finance's recommendations endpoint. News is sourced from Yahoo Finance market articles.</p>
    <p class=faq-q>What does "days left" mean?</p>
    <p>Days until the next earnings report date. We only show stocks within 14 days of reporting.</p>
    <p class=faq-q>Why do some numbers not match exactly?</p>
    <p>The analyst breakdown (Strong Buy / Buy / Hold / Sell) comes from Yahoo's historical recommendations data. The total count reflects analysts who have submitted ratings in that period. Numbers are sourced from the same endpoint for consistency.</p>
    <p class=faq-q>What does IV mean?</p>
    <p>Implied Volatility - how much the options market expects the stock to move. High IV stocks have larger straddle targets and greater score potential.</p>
    <p class=faq-q>Can I trade based on this?</p>
    <p>You can, but AI Market Cap is not responsible for any gains or losses. Options trading is high risk. This tool helps identify opportunities - the trade decision is always yours.</p>

    <div class=disclaimer>
        <strong>Disclaimer:</strong> AI Market Cap is for informational purposes only. Options data and price targets are estimates based on ATM straddles - actual results may vary. This is not a financial advisor service. Always do your own research before trading. AI Market Cap is not liable for any losses incurred from trades based on this data.
    </div>
</div>
</body></html>"""

with open(r'C:\Users\Tyler_AI\Desktop\about.html', 'w', encoding='utf-8') as f:
    f.write(about_html)
print('Done')