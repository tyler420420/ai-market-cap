import tweepy
client = tweepy.Client(
    consumer_key='REDACTED_X_CREDENTIAL',
    consumer_secret='REDACTED_X_CREDENTIAL',
    access_token='REDACTED_X_CREDENTIAL',
    access_token_secret='REDACTED_X_CREDENTIAL'
)
lines = [
    'Daily Top Strong Buy Targets 🎯 - aismarketcap.com',
    '1. SNOW 96 | $172 -> $194 (+12.7%)',
    '2. CRWD 92 | $663 -> $699 (+5.4%)',
    '3. PANW 91 | $260 -> $273 (+5.0%)',
    '4. ZS 91 | $182 -> $206 (+13.4%)',
    '5. ADSK 89 | $240 -> $263 (+9.4%)',
    '6. MRVL 89 | $196 -> $223 (+13.7%)',
    '#AIStocks #StockMarket #Nasdaq #OptionsTrading #Trading #Investing'
]
client.create_tweet(text='\n'.join(lines))
print('Posted')