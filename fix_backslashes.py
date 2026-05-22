with open('ai_earnings_scanner.py') as f:
    lines = f.readlines()
line538 = lines[537]
# Count and remove all backslashes
backslash_count = line538.count(chr(92))
print(f'Backslashes before: {backslash_count}')
lines[537] = line538.replace(chr(92), '')
backslash_count = lines[537].count(chr(92))
print(f'Backslashes after: {backslash_count}')
with open('ai_earnings_scanner.py', 'w') as f:
    f.writelines(lines)
print('Fixed!')