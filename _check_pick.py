with open('scanner.html', encoding='utf-8') as f:
    html = f.read()

# Find the "AI's Next Trade" or pick section
ai_pos = html.find("AI's Next Trade")
if ai_pos < 0:
    ai_pos = html.find('AI\'s Next Trade')
if ai_pos < 0:
    ai_pos = html.find('Next Trade')
if ai_pos < 0:
    ai_pos = html.find('Trade')
print(f'"Trade" found at: {ai_pos}')
if ai_pos >= 0:
    print(repr(html[ai_pos:ai_pos+500]))

# Check for double </script>
print(f'\nDouble </script>: {html.count("</script></script>")}')
print(f'</script> total: {html.count("</script>")}')
print(f'Last 100 chars: {repr(html[-100:])}')
