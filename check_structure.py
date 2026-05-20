with open('ai_earnings_57day_20260519_2312.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the ticker strip
ticker_pos = c.find('id="tickerStrip"')
print(f'Ticker strip at: {ticker_pos}')
ticker_end = c.find('</div>', ticker_pos) + 6
print(f'Ticker strip section: {repr(c[ticker_pos:ticker_end][:500])}')

print()
# Find the scanner container / table
table_pos = c.find('<table id="stockTable"')
print(f'Table at: {table_pos}')

# Show full style block
style_start = c.find('<style>')
style_end = c.find('</style>')
style = c[style_start:style_end]
print(f'\nFull CSS ({len(style)} chars):')
print(style)