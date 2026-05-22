import os
files = [
    'C:/Users/Tyler_AI/.mavis/sessions/mvs_41a119d03ae849d59a2cdecd57e77d10/workspace/ai_earnings_57day_20260520_0037.html',
    'C:/Users/Tyler_AI/Desktop/test_scanner.html',
    'C:/Users/Tyler_AI/Desktop/14 days earning screener.html'
]
for f in files:
    size = os.path.getsize(f)
    with open(f, 'rb') as fh:
        raw = fh.read()
    print(f'{os.path.basename(f)}: {size} bytes')
    print(f'  updateArrows: {b"updateArrows" in raw}')
    print(f'  sorted-asc: {b"sorted-asc" in raw}')
    print(f'  onclick-sortBy: {b"onclick=" in raw and b"sortBy" in raw}')
    print(f'  cursor-pointer: {b"cursor:pointer" in raw}')
    print()