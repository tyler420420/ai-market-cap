with open('ai_earnings_57day_20260519_2256.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Get the full first script block
s = c.find('<script>')
e = c.find('</script>')
script = c[s+8:e]
print(f'Script length: {len(script)}')
print(f'Script:\n{script}')
print()

# Try to parse the JSON part
import json
json_start = script.find('[')
json_end = script.rfind(']')
json_str = script[json_start:json_end+1]
print(f'JSON string length: {len(json_str)}')
try:
    data = json.loads(json_str)
    print(f'Parsed {len(data)} rows')
except Exception as ex:
    print(f'JSON parse error: {ex}')
    # Show around the error
    print(repr(script[json_start:json_start+500]))

# Check if there are any JS syntax errors by counting things
print(f'\nOpen braces: {script.count("{")}')
print(f'Close braces: {script.count("}")}')
print(f'Open parens: {script.count("(")}')
print(f'Close parens: {script.count(")")}')
print(f'Open brackets: {script.count("[")}')
print(f'Close brackets: {script.count("]")}')