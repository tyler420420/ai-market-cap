import subprocess, sys, json
from pathlib import Path

# Run the scanner
print("Running scanner...")
result = subprocess.run(
    [sys.executable, "ai_earnings_scanner.py"],
    capture_output=True, text=True, encoding='utf-8', errors='replace',
    timeout=180, cwd=str(Path(__file__).parent)
)
print("Done. Checking scanner_data.json...")

with open('scanner_data.json', 'r') as f:
    data = json.load(f)

print(f"Stocks: {len(data)}")
for s in data[:5]:
    print(f"  {s['ticker']}: price=${s['price']}, days={s['days_left']}, earnings={s['earnings_date']}")
for s in data:
    if s['ticker'] == 'MU':
        print(f"\nMU: price=${s['price']}, days={s['days_left']}, earnings={s['earnings_date']}")
        break
