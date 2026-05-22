content = open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\scanner_web.py', encoding='utf-8').read()

# Extract about_html from scanner_web.py
start = content.find('about_html = """<!DOCTYPE html>')
end = content.find('</html>"""', start) + len('</html>"""')
about_html = content[start+len('about_html = '):end]

with open(r'C:\Users\Tyler_AI\Desktop\about.html', 'w', encoding='utf-8') as f:
    f.write(about_html)
print('Done')