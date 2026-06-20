from pathlib import Path
html = Path(r'C:\Users\Tyler_AI\Desktop\test_scanner.html').read_text()
ai = html.find("AI's Suggested Trade")
print(html[ai:ai+400])
