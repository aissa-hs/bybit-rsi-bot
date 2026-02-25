from config import RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD


class TradingStrategy:
    def __init__(self):
        self.min_score_buy = 5
        self.min_score_sell = 5
        self.strong_multiplier = 1.5
    
    def analyze_signal(self, a, price, higher_tf_trend="NEUTRAL", volume_confirmed=True):
        rsi = a['rsi']
        macd_hist = a['macd'][2] if a['macd'] else 0
        macd_line = a['macd'][0] if a['macd'] and a['macd'][0] else 0
        signal_line = a['macd'][1] if a['macd'] and a['macd'][1] else 0
        stoch_k = a['stochastic'][0] if a['stochastic'] else 50
        stoch_d = a['stochastic'][1] if a['stochastic'] and len(a['stochastic']) > 1 else 50
        adx = a['adx'] if a['adx'] else 0
        cci = a['cci'] if a['cci'] else 0
        
        kdj_k = a['kdj'][0] if a['kdj'] else 50
        kdj_d = a['kdj'][1] if a['kdj'] and len(a['kdj']) > 1 else 50
        kdj_j = a['kdj'][2] if a['kdj'] and len(a['kdj']) > 2 else 50
        
        vwap = a['vwap'] if a['vwap'] else price
        obv_trend = a.get('obv_trend', 'NEUTRAL')
        volume_profile = a.get('volume_profile', 1.0)
        divergence = a.get('divergence', 'NONE')
        
        buy_score = 0
        sell_score = 0
        indicators = []
        
        if rsi < RSI_OVERSOLD:
            buy_score += 3
            indicators.append("RSI Oversold")
        elif rsi > RSI_OVERBOUGHT:
            sell_score += 3
            indicators.append("RSI Overbought")
        
        if rsi < 40:
            buy_score += 1
        elif rsi > 60:
            sell_score += 1
        
        if divergence == "BULLISH_DIVERGENCE":
            buy_score += 4
            indicators.append("Bullish Divergence")
        elif divergence == "BEARISH_DIVERGENCE":
            sell_score += 4
            indicators.append("Bearish Divergence")
        
        if macd_hist > 0:
            buy_score += 2
            if macd_hist > 0.5:
                indicators.append("MACD Strong Bullish")
        elif macd_hist < 0:
            sell_score += 2
            if macd_hist < -0.5:
                indicators.append("MACD Strong Bearish")
        
        if macd_line > signal_line:
            buy_score += 1
        elif macd_line < signal_line:
            sell_score += 1
        
        if kdj_k < 20 and kdj_d < 20:
            buy_score += 2
            indicators.append("KDJ Oversold")
        elif kdj_k > 80 and kdj_d > 80:
            sell_score += 2
            indicators.append("KDJ Overbought")
        
        if kdj_j < 0:
            buy_score += 1
        elif kdj_j > 100:
            sell_score += 1
        
        if cci < -100:
            buy_score += 2
            indicators.append("CCI Oversold")
        elif cci > 100:
            sell_score += 2
            indicators.append("CCI Overbought")
        
        if price > vwap:
            buy_score += 1
        elif price < vwap:
            sell_score += 1
        
        if stoch_k < 20:
            buy_score += 1
        elif stoch_k > 80:
            sell_score += 1
        
        if adx > 25:
            if higher_tf_trend == "UP":
                buy_score += 2
                indicators.append("HTF Trend Confirm")
            elif higher_tf_trend == "DOWN":
                sell_score += 2
                indicators.append("HTF Trend Confirm")
        
        if volume_profile > 1.5 and volume_confirmed:
            buy_score += 1
            sell_score += 1
            indicators.append("High Volume")
        
        if obv_trend == "BULLISH":
            buy_score += 1
        elif obv_trend == "BEARISH":
            sell_score += 1
        
        if a['sma_50'] and price > a['sma_50']:
            buy_score += 1
        elif a['sma_50'] and price < a['sma_50']:
            sell_score += 1
        
        if a['sma_200']:
            if price > a['sma_200']:
                buy_score += 1
            else:
                sell_score += 1
        
        result = "WAIT"
        if buy_score >= self.min_score_buy * self.strong_multiplier:
            result = "STRONG_BUY"
        elif buy_score >= self.min_score_buy:
            result = "BUY"
        elif sell_score >= self.min_score_sell * self.strong_multiplier:
            result = "STRONG_SELL"
        elif sell_score >= self.min_score_sell:
            result = "SELL"
        
        return result, max(buy_score, sell_score), indicators
    
    def get_higher_timeframe_trend(self, market_reader, symbol):
        tf_map = {"15m": "1h", "1h": "4h", "4h": "1d"}
        higher_tf = tf_map.get("15m", "1h")
        
        try:
            hr_market = market_reader.__class__(symbol, higher_tf)
            df = hr_market.get_klines(limit=50)
            if df is not None and len(df) > 50:
                closes = df['close'].values
                sma_20 = closes[-20:].mean()
                sma_50 = closes[-50:].mean() if len(closes) >= 50 else sma_20
                
                if sma_20 > sma_50:
                    return "UP"
                elif sma_20 < sma_50:
                    return "DOWN"
        except:
            pass
        
        return "NEUTRAL"
