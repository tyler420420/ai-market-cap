import yfinance as yf
stock = yf.Ticker("MU")
cal = stock.calendar
print("Calendar:", cal)
print("Earnings date:", cal.get('Earnings Date', 'N/A'))
print("Today:", __import__('datetime').date.today())