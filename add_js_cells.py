with open('ai_earnings_scanner.py', 'r') as f:
    content = f.read()

# Find the newsHtml call and add short_int and iv before it
# The pattern is: html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';
old_pattern = "html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"
new_pattern = "html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td style=\"color:#fff\">'+r.short_int+'%</td>';html+='<td style=\"color:#fff\">'+r.iv+'%</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    with open('ai_earnings_scanner.py', 'w') as f:
        f.write(content)
    print('Fixed JS rendering!')
else:
    print('Pattern not found')
    # Debug
    idx = content.find('fmtMktcap(r.mktcap)')
    if idx > 0:
        print('Context:', repr(content[idx:idx+100]))