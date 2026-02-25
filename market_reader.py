import numpy as np
import pandas as pd
import requests


class MarketReader:
    def __init__(self, symbol="BTCUSDT", timeframe="5m"):
        self.symbol = symbol.upper()
        self.timeframe = timeframe
        self.base_url = "https://api.binance.com/api/v3"
    
    def get_klines(self, limit=300):
        try:
            url = f"{self.base_url}/klines"
            params = {"symbol": self.symbol, "interval": self.timeframe, "limit": limit}
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if isinstance(data, dict) and 'code' in data:
                return None
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            return df
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_current_price(self):
        try:
            url = f"{self.base_url}/ticker/price"
            response = requests.get(url, params={"symbol": self.symbol}, timeout=10)
            return float(response.json()['price'])
        except:
            return None
    
    def get_24h_stats(self):
        try:
            url = f"{self.base_url}/ticker/24hr"
            response = requests.get(url, params={"symbol": self.symbol}, timeout=10)
            data = response.json()
            return {
                'price_change': float(data['priceChange']),
                'price_change_percent': float(data['priceChangePercent']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice']),
                'volume': float(data['volume']),
                'quote_volume': float(data['quoteVolume'])
            }
        except:
            return None
    
    def calculate_sma(self, closes, period):
        if len(closes) < period:
            return None
        return pd.Series(closes).rolling(window=period).mean().iloc[-1]
    
    def calculate_ema(self, closes, period):
        if len(closes) < period:
            return None
        return pd.Series(closes).ewm(span=period, adjust=False).mean().iloc[-1]
    
    def calculate_rsi(self, closes, period=14):
        if len(closes) < period + 1:
            return 50
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = pd.Series(gains).rolling(window=period).mean().iloc[-1]
        avg_losses = pd.Series(losses).rolling(window=period).mean().iloc[-1]
        
        if avg_losses == 0:
            return 100
        rs = avg_gains / avg_losses
        return 100 - (100 / (1 + rs))
    
    def calculate_macd(self, closes):
        if len(closes) < 26:
            return None, None, None
        
        ema12 = pd.Series(closes).ewm(span=12, adjust=False).mean()
        ema26 = pd.Series(closes).ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        
        return macd_line.iloc[-1], signal_line.iloc[-1], macd_line.iloc[-1] - signal_line.iloc[-1]
    
    def calculate_bollinger_bands(self, closes, period=20, std_dev=2):
        if len(closes) < period:
            return None, None, None
        
        sma = pd.Series(closes).rolling(window=period).mean()
        std = pd.Series(closes).rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return upper.iloc[-1], sma.iloc[-1], lower.iloc[-1]
    
    def calculate_stochastic(self, highs, lows, closes, period=14):
        if len(closes) < period:
            return None, None
        
        highest = pd.Series(highs).rolling(window=period).max()
        lowest = pd.Series(lows).rolling(window=period).min()
        
        k = 100 * (closes[-1] - lowest.iloc[-1]) / (highest.iloc[-1] - lowest.iloc[-1] + 1e-10)
        d = pd.Series([k]).rolling(window=3).mean().iloc[-1]
        
        return k, d
    
    def calculate_adx(self, highs, lows, closes, period=14):
        if len(closes) < period + 1:
            return None
        
        highs = np.array(highs)
        lows = np.array(lows)
        closes = np.array(closes)
        
        plus_dm = np.where((highs[1:] - highs[:-1]) > (lows[:-1] - lows[1:]),
                          np.maximum(highs[1:] - highs[:-1], 0), 0)
        minus_dm = np.where((lows[:-1] - lows[1:]) > (highs[1:] - highs[:-1]),
                            np.maximum(lows[:-1] - lows[1:], 0), 0)
        
        tr = np.maximum(highs[1:] - lows[1:], 
                       np.maximum(abs(highs[1:] - closes[:-1]),
                                 abs(lows[1:] - closes[:-1])))
        
        plus_di = 100 * np.mean(plus_dm[-period:]) / (np.mean(tr[-period:]) + 1e-10)
        minus_di = 100 * np.mean(minus_dm[-period:]) / (np.mean(tr[-period:]) + 1e-10)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = dx
        
        return adx
    
    def calculate_atr(self, highs, lows, closes, period=14):
        if len(closes) < period + 1:
            return None
        
        highs = np.array(highs)
        lows = np.array(lows)
        closes = np.array(closes)
        
        tr = np.maximum(highs[1:] - lows[1:], 
                       np.maximum(abs(highs[1:] - closes[:-1]),
                                 abs(lows[1:] - closes[:-1])))
        
        return np.mean(tr[-period:])
    
    def find_support_resistance(self, closes, highs, lows, lookback=50):
        if len(closes) < lookback:
            return None, None
        
        recent_closes = closes[-lookback:]
        recent_highs = highs[-lookback:]
        recent_lows = lows[-lookback:]
        
        resistance = np.max(recent_highs)
        support = np.min(recent_lows)
        
        return support, resistance
    
    def calculate_sl_tp(self, price, signal_type, atr=None, support=None, resistance=None):
        risk_reward = 2.5
        
        if signal_type == "BUY":
            if support and support < price:
                sl = min(support * 0.998, price - (atr * 1.5 if atr else price * 0.02))
            elif atr:
                sl = price - min(atr * 1.5, price * 0.025)
            else:
                sl = price * 0.975
            
            sl = min(sl, price * 0.975)
            
            risk = price - sl
            
            tp1 = price + risk * 1.0
            tp2 = price + risk * 2.0
            tp3 = price + risk * 2.5
            
            if resistance and resistance > price:
                tp3 = min(tp3, resistance * 0.998)
            
            return {
                'sl': sl,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'sl_pct': ((sl - price) / price) * 100,
                'tp1_pct': ((tp1 - price) / price) * 100,
                'tp2_pct': ((tp2 - price) / price) * 100,
                'tp3_pct': ((tp3 - price) / price) * 100,
                'risk_reward': risk_reward,
                'partials': [
                    {'target': tp1, 'pct': 25, 'action': 'move_sl_to_breakeven'},
                    {'target': tp2, 'pct': 50, 'action': 'trail_stop'},
                    {'target': tp3, 'pct': 25, 'action': 'close_all'}
                ]
            }
        
        elif signal_type == "SELL":
            if resistance and resistance > price:
                sl = max(resistance * 1.002, price + (atr * 1.5 if atr else price * 0.02))
            elif atr:
                sl = price + min(atr * 1.5, price * 0.025)
            else:
                sl = price * 1.025
            
            sl = max(sl, price * 1.025)
            
            risk = sl - price
            
            tp1 = price - risk * 1.0
            tp2 = price - risk * 2.0
            tp3 = price - risk * 2.5
            
            if support and support < price:
                tp3 = max(tp3, support * 1.002)
            
            return {
                'sl': sl,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'sl_pct': ((sl - price) / price) * 100,
                'tp1_pct': ((tp1 - price) / price) * 100,
                'tp2_pct': ((tp2 - price) / price) * 100,
                'tp3_pct': ((tp3 - price) / price) * 100,
                'risk_reward': risk_reward,
                'partials': [
                    {'target': tp1, 'pct': 25, 'action': 'move_sl_to_breakeven'},
                    {'target': tp2, 'pct': 50, 'action': 'trail_stop'},
                    {'target': tp3, 'pct': 25, 'action': 'close_all'}
                ]
            }
        
        return None
    
    def calculate_kdj(self, highs, lows, closes, period=9):
        if len(closes) < period:
            return None, None, None
        
        highs = np.array(highs)
        lows = np.array(lows)
        closes = np.array(closes)
        
        lowest_low = pd.Series(lows).rolling(window=period).min()
        highest_high = pd.Series(highs).rolling(window=period).max()
        
        rsv = 100 * (closes - lowest_low) / (highest_high - lowest_low + 1e-10)
        
        k = rsv.ewm(span=3, adjust=False).mean()
        d = k.ewm(span=3, adjust=False).mean()
        j = 3 * k - 2 * d
        
        return k.iloc[-1], d.iloc[-1], j.iloc[-1]
    
    def calculate_vwap(self, highs, lows, closes, volumes):
        if len(closes) < 1:
            return None
        
        if isinstance(volumes, np.ndarray):
            volumes = pd.Series(volumes)
        if isinstance(closes, np.ndarray):
            closes = pd.Series(closes)
        if isinstance(highs, np.ndarray):
            highs = pd.Series(highs)
        if isinstance(lows, np.ndarray):
            lows = pd.Series(lows)
        
        typical_price = (highs + lows + closes) / 3
        cumulative_tpv = (typical_price * volumes).cumsum()
        cumulative_volume = volumes.cumsum()
        
        vwap = cumulative_tpv / cumulative_volume
        return vwap.iloc[-1]
    
    def calculate_cci(self, highs, lows, closes, period=20):
        if len(closes) < period:
            return None
        
        if isinstance(closes, np.ndarray):
            closes = pd.Series(closes)
        if isinstance(highs, np.ndarray):
            highs = pd.Series(highs)
        if isinstance(lows, np.ndarray):
            lows = pd.Series(lows)
        
        typical_price = (highs + lows + closes) / 3
        sma = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        
        cci = (typical_price - sma) / (0.015 * mean_deviation + 1e-10)
        return cci.iloc[-1]
    
    def calculate_obv(self, closes, volumes):
        if len(closes) < 2:
            return None
        
        if isinstance(closes, np.ndarray):
            closes = pd.Series(closes)
        if isinstance(volumes, np.ndarray):
            volumes = pd.Series(volumes)
        
        obv = pd.Series(index=range(len(closes)), dtype=float)
        obv.iloc[0] = 0
        
        for i in range(1, len(closes)):
            if closes.iloc[i] > closes.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volumes.iloc[i]
            elif closes.iloc[i] < closes.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volumes.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv.iloc[-1]
    
    def calculate_obv_trend(self, closes, volumes, period=10):
        if len(closes) < period + 1:
            return "NEUTRAL"
        
        if isinstance(closes, np.ndarray):
            closes = pd.Series(closes)
        if isinstance(volumes, np.ndarray):
            volumes = pd.Series(volumes)
        
        obv_values = []
        obv = 0
        for i in range(len(closes)):
            if i == 0:
                obv = 0
            elif closes.iloc[i] > closes.iloc[i-1]:
                obv += volumes.iloc[i]
            elif closes.iloc[i] < closes.iloc[i-1]:
                obv -= volumes.iloc[i]
            obv_values.append(obv)
        
        if len(obv_values) < period:
            return "NEUTRAL"
        
        recent_obv = obv_values[-period:]
        if all(recent_obv[i] < recent_obv[i+1] for i in range(period-1)):
            return "BULLISH"
        elif all(recent_obv[i] > recent_obv[i+1] for i in range(period-1)):
            return "BEARISH"
        return "NEUTRAL"
    
    def calculate_volume_profile(self, volumes, period=20):
        if len(volumes) < period:
            return 1.0
        
        if isinstance(volumes, np.ndarray):
            volumes = pd.Series(volumes)
        
        avg_volume = volumes.iloc[-period:].mean()
        current_volume = volumes.iloc[-1]
        
        return current_volume / (avg_volume + 1e-10)
    
    def detect_divergence(self, closes, rsi_values, period=20):
        if len(closes) < period or len(rsi_values) < period:
            return "NONE"
        
        price_highs = pd.Series(closes).rolling(window=period).max()
        price_lows = pd.Series(closes).rolling(window=period).min()
        rsi_highs = pd.Series(rsi_values).rolling(window=period).max()
        rsi_lows = pd.Series(rsi_values).rolling(window=period).min()
        
        recent_bars = 5
        
        price_new_high = closes[-1] >= price_highs.iloc[-1] * 0.99
        rsi_lower_high = rsi_values[-1] < rsi_highs.iloc[-1] * 0.95
        
        if price_new_high and rsi_lower_high:
            return "BEARISH_DIVERGENCE"
        
        price_new_low = closes[-1] <= price_lows.iloc[-1] * 1.01
        rsi_higher_low = rsi_values[-1] > rsi_lows.iloc[-1] * 1.05
        
        if price_new_low and rsi_higher_low:
            return "BULLISH_DIVERGENCE"
        
        return "NONE"
    
    def get_volume_status(self, volumes, period=20):
        if len(volumes) < period:
            return "normal"
        avg_volume = np.mean(volumes[-period:])
        current_volume = volumes[-1]
        if current_volume > avg_volume * 1.5:
            return "high"
        elif current_volume < avg_volume * 0.5:
            return "low"
        return "normal"
    
    def analyze(self):
        df = self.get_klines(limit=300)
        if df is None:
            return None
        
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        volumes = df['volume'].values
        
        price = closes[-1]
        atr = self.calculate_atr(highs, lows, closes)
        support, resistance = self.find_support_resistance(closes, highs, lows)
        
        rsi_value = self.calculate_rsi(closes)
        
        analysis = {
            'price': price,
            'rsi': rsi_value,
            'sma_50': self.calculate_sma(closes, 50),
            'sma_200': self.calculate_sma(closes, 200),
            'ema_50': self.calculate_ema(closes, 50),
            'ema_200': self.calculate_ema(closes, 200),
            'macd': self.calculate_macd(closes),
            'bollinger': self.calculate_bollinger_bands(closes),
            'stochastic': self.calculate_stochastic(highs, lows, closes),
            'adx': self.calculate_adx(highs, lows, closes),
            'atr': atr,
            'support': support,
            'resistance': resistance,
            'volume_status': self.get_volume_status(volumes),
            'change_24h': 0,
            'kdj': self.calculate_kdj(highs, lows, closes),
            'vwap': self.calculate_vwap(highs, lows, closes, volumes),
            'cci': self.calculate_cci(highs, lows, closes),
            'obv': self.calculate_obv(closes, volumes),
            'obv_trend': self.calculate_obv_trend(closes, volumes),
            'volume_profile': self.calculate_volume_profile(volumes),
            'divergence': self.detect_divergence(closes, [rsi_value] * len(closes))
        }
        
        stats = self.get_24h_stats()
        if stats:
            analysis['change_24h'] = stats['price_change_percent']
        
        return analysis
