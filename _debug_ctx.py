with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', encoding='utf-8') as f:
    content = f.read()

# What's around position 29548 (second <script>)
ctx = content[29500:29610]
print(f'Around second <script> (29500-29610):')
print(repr(ctx))
print()

# What's around position 27800 (tbody area)
ctx2 = content[27750:27850]
print(f'Around tbody (27750-27850):')
print(repr(ctx2))
print()

# What's around position 28700 (after tbody)
ctx3 = content[28650:28750]
print(f'After tbody (28650-28750):')
print(repr(ctx3))
