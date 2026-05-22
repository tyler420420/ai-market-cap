with open('ai_earnings_57day_20260520_0115.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the querySelector for th with data-col
idx = c.find("querySelector('th[data-col=")
with open('query_check.txt', 'w', encoding='utf-8') as f:
    f.write(c[idx:idx+100])

# Find where updateArrows is called
idx2 = c.find('updateArrows();}')
with open('render_end.txt', 'w', encoding='utf-8') as f:
    f.write(c[idx2-100:idx2+20])

# Check if rowsData is valid JSON by counting items
import json
rd_start = c.find('var rowsData=')
rd_end = c.find(';', rd_start + 13)
rd_json = c[rd_start+13:rd_end]
with open('rowsdata_check.txt', 'w', encoding='utf-8') as f:
    try:
        data = json.loads(rd_json)
        f.write('rowsData is valid JSON, length: ' + str(len(data)))
        f.write('\nFirst item: ' + str(data[0]))
    except Exception as e:
        f.write('rowsData JSON error: ' + str(e))

print('Done')