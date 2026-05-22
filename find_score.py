content = open('ai_earnings_today.html').read()
idx = content.find("'+c+'")
print(content[idx-80:idx+200])