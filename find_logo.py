import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

idx = content.find('height:34px')
print(content[max(0, idx-300):idx+300])