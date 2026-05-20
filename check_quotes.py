with open('C:/Users/Tyler_AI/.mavis/sessions/mvs_41a119d03ae849d59a2cdecd57e77d10/workspace/ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

line480 = lines[479]  # 0-indexed, so line 480
print('Line 480 raw:', repr(line480))
print()
print('Single quotes:', line480.count("'"))
print('Double quotes:', line480.count('"'))
print()
# Find all single quote positions
print('Single quote positions:')
for i, ch in enumerate(line480):
    if ch == "'":
        ctx = line480[max(0, i-15):i+15]
        print(f'  pos {i}: {repr(ctx)}')