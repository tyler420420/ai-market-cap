with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

line529 = lines[528]
# Find the specific problematic section
bad_area = line529.find('color:#ffcc00">')
if bad_area >= 0:
    print('Around the problematic hold line:')
    print(repr(line529[bad_area-50:bad_area+80]))
    print()
    # Find the position of r.buy and r.hold
    buy_pos = line529.find("r.buy")
    hold_pos = line529.find("r.hold")
    print(f"r.buy at char: {buy_pos}")
    print(f"r.hold at char: {hold_pos}")
    print()
    # Show the exact buy and hold td lines
    # Search backward from r.buy to find the html+= that starts it
    buy_start = line529.rfind("html+='", 0, buy_pos)
    print(f"Buy td line: {repr(line529[buy_start:buy_pos+30])}")
    hold_start = line529.rfind("html+='", 0, hold_pos)
    print(f"Hold td line: {repr(line529[hold_start:hold_pos+30])}")