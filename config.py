"""
Configuration file for RSI Market Reader Bot
"""
import os

# Market Data Settings
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
TIMEFRAME = "15m"

# RSI Settings
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Telegram Notifications (use env vars on production)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8593238089:AAFHSrO4S-P0ahGp-Ox2DikSV07jRXylUKo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "6431370638")

# Update interval (in seconds)
UPDATE_INTERVAL = 300  # 5 minutes

# Login Password (use env var on production)
LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD", "aissa2005go")

# Bybit API (optional - for test_connection.py and backtest.py)
API_KEY = os.environ.get("API_KEY", "")
API_SECRET = os.environ.get("API_SECRET", "")
TESTNET = True
