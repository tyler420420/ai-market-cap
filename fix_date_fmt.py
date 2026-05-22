c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
# Add a formatting function for earnings date in the HTML generation section
# Change the earnings_date in rowsData to be formatted nicely
old = "'earnings_date': stock.earnings_date,"
new = "'earnings_date': stock.earnings_date.replace('2026-','2026\\n') if stock.earnings_date else '',"
c=c.replace(old,new)
# Change in static rows too
old2 = "static_rows += '<td>' + r['earnings_date'] + '</td>'"
new2 = "edate = r['earnings_date']\n        import datetime\n        try:\n            dt = datetime.datetime.strptime(edate, '%Y-%m-%d')\n            edate_fmt = dt.strftime('%b %d, %Y')\n        except:\n            edate_fmt = edate or ''\n        static_rows += '<td style=\"white-space:pre-line;font-size:0.85em\">' + edate_fmt + '</td>'"
# Can't do multi-line replace easily, let me use a simpler approach
# Just change the replace logic
new2 = "# format earnings date\n        edate = r['earnings_date']\n        import datetime as dt2\n        try:\n            d = dt2.datetime.strptime(edate, '%Y-%m-%d')\n            edate_fmt = d.strftime('%b %d\\n%Y')\n        except:\n            edate_fmt = edate or ''\n        static_rows += '<td style=\"white-space:pre-line;font-size:0.85em\">' + edate_fmt + '</td>'"
c=c.replace(old2, new2)
# Also fix the header to say Next Earnings with <br>
open('ai_earnings_scanner.py','w',encoding='utf-8').write(c)
print('Done')