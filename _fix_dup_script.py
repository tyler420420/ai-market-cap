with open('scanner.html', encoding='utf-8') as f:
    html = f.read()

# Fix double </script> tag
html = html.replace(';</script></script>', ';</script>')

with open('scanner.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Fixed: {len(html)} bytes')
print(f'Double </script>: {html.count("</script></script>")}')
print(f'Last 50 chars: {repr(html[-50:])}')
