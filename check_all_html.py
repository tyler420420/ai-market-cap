import glob

files = sorted(glob.glob('ai_earnings_57day_*.html'))
for f in files:
    with open(f, encoding='utf-8') as fh:
        c = fh.read()
    print(f'{f}: {len(c)} bytes, has rowsData={"rowsData" in c}, has stockTable={"stockTable" in c}')