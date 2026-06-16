path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the style end line and insert mobile CSS before it
for i, line in enumerate(lines):
    if '</style></head><body>' in line:
        mobile = "    html += '@media(max-width:600px){body{padding:5px;font-size:13px}#stockTable{font-size:12px;overflow-x:auto;display:block}#stockTable thead,#stockTable tbody,#stockTable tr,#stockTable td,#stockTable th{display:block}#stockTable thead{position:absolute;top:-9999px;left:-9999px}#stockTable tr{border:1px solid #30363d;border-radius:8px;margin-bottom:10px;padding:8px;background:#161b22}#stockTable td{position:relative;padding:3px 8px;border:none;font-size:12px;line-height:1.4}#stockTable td:before{content:attr(data-label);font-weight:700;color:#58a6ff;margin-right:6px}#stockTable td.earn-cell{font-size:11px}#stockTable td a{font-size:13px!important}}'\n"
        lines.insert(i, mobile)
        print(f'Inserted mobile CSS at line {i+1}')
        break

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Done')