"""One-off manual tweet helper.

SECURITY: the X API keys were previously hardcoded directly in this file and
are compromised - they must be rotated at the X developer portal. They are now
read from the environment only. Run with all four set:

    X_API_KEY=... X_API_SECRET=... X_ACCESS_TOKEN=... X_ACCESS_TOKEN_SECRET=... python post_tweet.py
"""
import os
import sys

import tweepy

REQUIRED = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
missing = [k for k in REQUIRED if not os.environ.get(k)]
if missing:
    sys.exit(f"Refusing to post: missing env vars {', '.join(missing)}")

client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
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