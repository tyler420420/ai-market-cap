with open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html', 'r', encoding='utf-8') as f:
    h = f.read()

print('Strong Buy=5:', '>5</span> <span style="color:#8b949e">Watch' in h)
print('Watch=5:', '<span style="font-weight:bold;color:#58a6ff">5</span> <span style="color:#8b949e">Watch' in h)
print('Watch=7 (old):', '<span style="font-weight:bold;color:#58a6ff">7</span> <span style="color:#8b949e">Watch' in h)
print('3 Day bold in rowsData:', 'pe_target' in h)
