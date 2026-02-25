import requests
import time
from datetime import datetime, timedelta


class NewsScanner:
    def __init__(self):
        self.cache_time = 0
        self.cache_ttl = 3600
        self.cached_sentiment = None
        self.base_url = "https://api.binance.com/api/v3"
    
    def get_market_sentiment_from_prices(self, coins=None):
        try:
            if not coins:
                coins = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
            
            total_change = 0
            count = 0
            
            for symbol in coins[:5]:
                try:
                    url = f"{self.base_url}/ticker/24hr"
                    r = requests.get(url, params={"symbol": symbol}, timeout=5)
                    if r.status_code == 200:
                        data = r.json()
                        total_change += float(data.get('priceChangePercent', 0))
                        count += 1
                except:
                    pass
            
            if count == 0:
                return "NEUTRAL"
            
            avg_change = total_change / count
            
            if avg_change > 2:
                return "BULLISH"
            elif avg_change < -2:
                return "BEARISH"
            return "NEUTRAL"
        except:
            return "NEUTRAL"
    
    def get_market_sentiment(self, coins=None, force=False):
        now = time.time()
        if not force and self.cached_sentiment and (now - self.cache_time) < self.cache_ttl:
            return self.cached_sentiment
        
        sentiment = self.get_market_sentiment_from_prices(coins)
        
        self.cached_sentiment = {
            "sentiment": sentiment,
            "timestamp": now,
            "method": "price_based"
        }
        self.cache_time = now
        return self.cached_sentiment
    
    def should_block_signal(self, signal_type, coins=None):
        sentiment_data = self.get_market_sentiment(coins)
        sentiment = sentiment_data.get("sentiment", "NEUTRAL")
        
        if signal_type in ["STRONG_BUY", "BUY"] and sentiment == "BEARISH":
            return True, f"Signal blocked: Market sentiment is BEARISH"
        if signal_type in ["STRONG_SELL", "SELL"] and sentiment == "BULLISH":
            return True, f"Signal blocked: Market sentiment is BULLISH"
        
        return False, None
    
    def get_news_summary(self):
        sentiment = self.get_market_sentiment()
        emoji = "🟢" if sentiment["sentiment"] == "BULLISH" else "🔴" if sentiment["sentiment"] == "BEARISH" else "⚪"
        return f"📰 Market Sentiment: {emoji} {sentiment['sentiment']}"


if __name__ == "__main__":
    scanner = NewsScanner()
    print("Testing news scanner...")
    result = scanner.get_market_sentiment(force=True)
    print(f"Sentiment: {result}")
