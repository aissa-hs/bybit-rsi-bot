#!/usr/bin/env python3
"""
RSI Trading Bot - Advanced Multi-Indicator Signal Sender
With news sentiment, multi-timeframe analysis, and improved SL/TP
"""

import time
import requests
import json
import os
from datetime import datetime
from market_reader import MarketReader
from news_scanner import NewsScanner
from trading_strategy import TradingStrategy
from config import (
    SYMBOLS, TIMEFRAME,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, UPDATE_INTERVAL
)


class TelegramBot:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "Mozilla/5.0"})
    
    def send_message(self, text, parse_mode="HTML", retries=3):
        for attempt in range(retries):
            try:
                url = f"{self.api_url}/sendMessage"
                payload = {"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode}
                response = self._session.post(url, json=payload, timeout=30)
                if response.status_code == 200:
                    return True
                elif response.status_code == 429:
                    wait_time = int(response.json().get("parameters", {}).get("retry_after", 60))
                    print(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
            except requests.exceptions.Timeout:
                print(f"Telegram timeout (attempt {attempt+1}/{retries}), retrying...")
                time.sleep(5)
            except Exception as e:
                print(f"Telegram error: {e}")
                time.sleep(2)
        print("Failed to send Telegram message after retries")
        return False


def format_signal(symbol, a, sl_tp, indicators, strategy):
    price = a['price']
    rsi = a['rsi']
    change = a['change_24h']
    macd_hist = a['macd'][2] if a['macd'] else 0
    kdj_j = a['kdj'][2] if a['kdj'] and len(a['kdj']) > 2 else 0
    cci = a['cci'] if a['cci'] else 0
    
    signal, score, _ = strategy.analyze_signal(a, price)
    
    if signal == "WAIT":
        return None
    
    signal_emoji = "🟢" if "BUY" in signal else "🔴"
    signal_text = signal.replace("_", " ")
    
    msg = f"🚨 <b>{signal_text}</b> 🚨\n\n"
    msg += f"📈 <b>{symbol}</b>\n"
    msg += f"💰 Price: ${price:,.2f}\n"
    msg += f"📊 Change 24h: {change:+.2f}%\n\n"
    msg += f"📉 <b>Indicators:</b>\n"
    msg += f"• RSI: {rsi:.1f}\n"
    msg += f"• MACD: {macd_hist:+.4f}\n"
    msg += f"• KDJ: {kdj_j:.1f}\n"
    msg += f"• CCI: {cci:.1f}\n"
    
    if indicators:
        msg += f"\n🔔 <b>Signals:</b>\n"
        for ind in indicators[:4]:
            msg += f"• {ind}\n"
    
    if sl_tp:
        rr = sl_tp.get('risk_reward', 2.0)
        msg += f"\n🛡️ <b>Stop Loss:</b> ${sl_tp['sl']:,.2f} ({sl_tp['sl_pct']:+.1f}%)\n"
        msg += f"🎯 <b>Take Profit:</b> R:R = 1:{rr}\n"
        msg += f"   TP1: ${sl_tp['tp1']:,.2f} ({sl_tp['tp1_pct']:+.1f}%) - 25%\n"
        msg += f"   TP2: ${sl_tp['tp2']:,.2f} ({sl_tp['tp2_pct']:+.1f}%) - 50%\n"
        msg += f"   TP3: ${sl_tp['tp3']:,.2f} ({sl_tp['tp3_pct']:+.1f}%) - 25%\n"
    
    msg += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    return msg


def format_summary(results, sentiment_info):
    msg = f"📊 <b>Market Summary</b> - {TIMEFRAME}\n"
    msg += f"{sentiment_info}\n\n"
    
    for symbol, a in results.items():
        if not a:
            continue
        
        strategy = TradingStrategy()
        signal, score, _ = strategy.analyze_signal(a, a['price'])
        
        emoji = "🟢" if "BUY" in signal else "🔴" if "SELL" in signal else "⚪"
        rsi = a['rsi']
        kdj_j = a['kdj'][2] if a['kdj'] and len(a['kdj']) > 2 else 0
        
        msg += f"{emoji} {symbol}: ${a['price']:,.0f}\n"
        msg += f"   RSI: {rsi:.0f} | KDJ: {kdj_j:.0f} | {signal}\n\n"
    
    msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    return msg


class SignalBot:
    def __init__(self):
        self.telegram = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.markets = {}
        self.last_signals = {sym: None for sym in SYMBOLS}
        self.cached_data = {}
        self.cache_time = 0
        self.cache_ttl = 60
        
        self.trade_history_file = "trade_history.json"
        self.trade_history = self.load_trade_history()
        self.pending_reviews = []
        
        self.news_scanner = NewsScanner()
        self.strategy = TradingStrategy()
        
        self.news_sentiment = self.news_scanner.get_market_sentiment(force=True)
        
        self.telegram.send_message(
            f"🤖 <b>Advanced RSI Bot Started</b>\n\n"
            f"📊 Pairs: {', '.join(SYMBOLS)}\n"
            f"⏱️ Timeframe: {TIMEFRAME}\n"
            f"🔄 Update: Every {UPDATE_INTERVAL//60} min\n"
            f"{self.news_scanner.get_news_summary()}"
        )
        print("Bot started!")
    
    def load_trade_history(self):
        if os.path.exists(self.trade_history_file):
            try:
                with open(self.trade_history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_trade_history(self):
        with open(self.trade_history_file, 'w') as f:
            json.dump(self.trade_history, f, indent=2)
    
    def record_trade(self, symbol, signal_type, price, sl_tp, indicators):
        trade = {
            'symbol': symbol,
            'signal_type': signal_type,
            'entry_price': price,
            'entry_time': datetime.now().isoformat(),
            'review_time': (datetime.now().timestamp() + 21600),
            'sl': sl_tp.get('sl') if sl_tp else None,
            'tp1': sl_tp.get('tp1') if sl_tp else None,
            'tp2': sl_tp.get('tp2') if sl_tp else None,
            'tp3': sl_tp.get('tp3') if sl_tp else None,
            'indicators': indicators,
            'status': 'pending_review'
        }
        self.trade_history.append(trade)
        self.save_trade_history()
        print(f"Trade recorded: {symbol} {signal_type} at ${price}")
    
    def review_trades(self):
        current_time = datetime.now().timestamp()
        trades_to_review = [t for t in self.trade_history if t.get('status') == 'pending_review' and t.get('review_time', 0) <= current_time]
        
        if not trades_to_review:
            return
        
        report = f"📊 <b>6-Hour Trade Review Report</b>\n\n"
        successful = 0
        failed = 0
        pending = 0
        
        for trade in trades_to_review:
            symbol = trade['symbol']
            signal_type = trade['signal_type']
            entry_price = trade['entry_price']
            sl = trade.get('sl')
            tp1 = trade.get('tp1')
            tp2 = trade.get('tp2')
            tp3 = trade.get('tp3')
            
            market = MarketReader(symbol, TIMEFRAME)
            current_price = market.get_current_price()
            
            if current_price is None:
                pending += 1
                continue
            
            trade_result = "PENDING"
            pnl_pct = 0
            
            if signal_type == "BUY":
                if sl and current_price <= sl:
                    trade_result = "STOP_LOSS"
                    pnl_pct = ((sl - entry_price) / entry_price) * 100
                    failed += 1
                elif tp3 and current_price >= tp3:
                    trade_result = "TAKE_PROFIT_3"
                    pnl_pct = ((tp3 - entry_price) / entry_price) * 100
                    successful += 1
                elif tp2 and current_price >= tp2:
                    trade_result = "TAKE_PROFIT_2"
                    pnl_pct = ((tp2 - entry_price) / entry_price) * 100
                    successful += 1
                elif tp1 and current_price >= tp1:
                    trade_result = "TAKE_PROFIT_1"
                    pnl_pct = ((tp1 - entry_price) / entry_price) * 100
                    successful += 1
                else:
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    trade_result = "IN_PROGRESS"
                    pending += 1
            elif signal_type == "SELL":
                if sl and current_price >= sl:
                    trade_result = "STOP_LOSS"
                    pnl_pct = ((entry_price - sl) / entry_price) * 100
                    failed += 1
                elif tp3 and current_price <= tp3:
                    trade_result = "TAKE_PROFIT_3"
                    pnl_pct = ((entry_price - tp3) / entry_price) * 100
                    successful += 1
                elif tp2 and current_price <= tp2:
                    trade_result = "TAKE_PROFIT_2"
                    pnl_pct = ((entry_price - tp2) / entry_price) * 100
                    successful += 1
                elif tp1 and current_price <= tp1:
                    trade_result = "TAKE_PROFIT_1"
                    pnl_pct = ((entry_price - tp1) / entry_price) * 100
                    successful += 1
                else:
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100
                    trade_result = "IN_PROGRESS"
                    pending += 1
            
            trade['status'] = trade_result
            trade['exit_price'] = current_price
            trade['pnl_pct'] = pnl_pct
            
            emoji = "✅" if "TAKE_PROFIT" in trade_result else "❌" if "STOP_LOSS" in trade_result else "⏳"
            report += f"{emoji} <b>{symbol}</b> {signal_type}\n"
            report += f"   Entry: ${entry_price:,.2f} | Current: ${current_price:,.2f}\n"
            report += f"   Result: {trade_result} ({pnl_pct:+.2f}%)\n"
            if trade.get('indicators'):
                report += f"   Signals: {', '.join(trade['indicators'][:3])}\n"
            report += f"   Entry Time: {trade['entry_time'][:16]}\n\n"
        
        report += f"📈 <b>Summary:</b>\n"
        report += f"   ✅ Successful: {successful}\n"
        report += f"   ❌ Failed: {failed}\n"
        report += f"   ⏳ Pending: {pending}\n"
        
        if successful + failed > 0:
            win_rate = (successful / (successful + failed)) * 100
            report += f"   📊 Win Rate: {win_rate:.1f}%\n"
        
        report += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        self.save_trade_history()
        self.telegram.send_message(report)
        print(f"Trade review report sent: {successful}W/{failed}L/{pending}P")
    
    def get_analysis(self, symbol, force=False):
        now = time.time()
        if not force and symbol in self.cached_data and (now - self.cache_time) < self.cache_ttl:
            return self.cached_data[symbol]
        
        if symbol not in self.markets:
            self.markets[symbol] = MarketReader(symbol, TIMEFRAME)
        
        a = self.markets[symbol].analyze()
        if a:
            self.cached_data[symbol] = a
            self.cache_time = now
        return a
    
    def calculate_sl_tp(self, price, signal_type):
        m = MarketReader('BTCUSDT', TIMEFRAME)
        df = m.get_klines(limit=50)
        if df is None:
            return None
        
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        
        atr = m.calculate_atr(highs, lows, closes)
        support, resistance = m.find_support_resistance(closes, highs, lows)
        
        sl_tp = m.calculate_sl_tp(price, signal_type, atr, support, resistance)
        if sl_tp:
            sl_tp['type'] = signal_type
        return sl_tp
    
    def check_signals(self):
        print("Checking signals...")
        
        if int(time.time()) % (UPDATE_INTERVAL * 2) < 30:
            self.news_sentiment = self.news_scanner.get_market_sentiment(force=True)
            print(f"News sentiment: {self.news_sentiment['sentiment']}")
        
        results = {}
        
        for symbol in SYMBOLS:
            a = self.get_analysis(symbol, force=True)
            results[symbol] = a
        
        sentiment_info = self.news_scanner.get_news_summary()
        self.telegram.send_message(format_summary(results, sentiment_info))
        
        for symbol, a in results.items():
            if not a:
                continue
            
            signal, score, indicators = self.strategy.analyze_signal(a, a['price'])
            
            blocked, reason = self.news_scanner.should_block_signal(signal, [symbol])
            if blocked:
                print(f"Blocked {signal} for {symbol}: {reason}")
                continue
            
            if signal.startswith("STRONG") or (signal in ["BUY", "SELL"] and score >= 6):
                last_sig = self.last_signals.get(symbol)
                if signal != last_sig:
                    self.last_signals[symbol] = signal
                    signal_type = "BUY" if "BUY" in signal else "SELL"
                    sl_tp = self.calculate_sl_tp(a['price'], signal_type)
                    msg = format_signal(symbol, a, sl_tp, indicators, self.strategy)
                    if msg:
                        self.telegram.send_message(msg)
                        self.record_trade(symbol, signal_type, a['price'], sl_tp, indicators)
                        print(f"Signal sent: {signal} {symbol} (Score: {score})")
    
    def run(self):
        print(f"Bot running - checking every {UPDATE_INTERVAL} seconds")
        self.last_review_time = time.time()
        
        self.check_signals()
        next_check = time.time() + UPDATE_INTERVAL
        
        while True:
            try:
                now = time.time()
                if now >= next_check:
                    self.check_signals()
                    next_check = now + UPDATE_INTERVAL
                
                if now - self.last_review_time >= 3600:
                    self.review_trades()
                    self.last_review_time = now
                
                time.sleep(10)
                
            except KeyboardInterrupt:
                print("\nBot stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(30)


if __name__ == "__main__":
    bot = SignalBot()
    bot.run()
