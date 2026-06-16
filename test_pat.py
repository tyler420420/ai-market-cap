path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

# Find the segment
idx = content.find(b"html+='<tr style")
if idx >= 0:
    chunk = content[idx:idx+50]
    print("Actual bytes:", chunk)
    print()
    print("As hex:", chunk.hex())
    print()

# My pattern
pattern = b"html+='<tr style\\\"background:'+bg+'\\\"><td>"
print("My pattern:", pattern)
print("As hex:", pattern.hex())

# Check if pattern is in content
if pattern in content:
    print("FOUND!")
else:
    print("NOT FOUND")
    
# Try with single backslash
pattern2 = b"html+='<tr style\"background:'+bg+'\"><td>"
print("\nPattern2:", pattern2)
print("As hex:", pattern2.hex())
if pattern2 in content:
    print("FOUND pattern2!")
else:
    print("NOT FOUND pattern2")