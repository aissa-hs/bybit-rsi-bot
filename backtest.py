#!/usr/bin/env python3
"""
Backtest the RSI strategy on historical Bybit data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pybit.unified_trading import HTTP
from config import SYMBOLS, TIMEFRAME, RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD, TESTNET

SYMBOL = SYMBOLS[0] if SYMBOLS else "BTCUSDT"

class RSI_backtest:
    def __init__(self):
        self.session = HTTP(testnet=TESTNET)
        self.initial_balance = 1000  # USDT
        self.balance = self.initial_balance
        self.position = None
        self.trades = []

    def get_historical_data(self, days=30):
        """Fetch historical kline data"""
        print(f"📊 Fetching {days} days of historical data...")
        limit = min(days * 96, 1000)  # 96 candles per day (15m)

        response = self.session.get_kline(
            category="linear",
            symbol=SYMBOL,
            interval=TIMEFRAME,
            limit=limit
        )

        if response['retCode'] == 0:
            data = response['result']['list']
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['open'] = df['open'].astype(float)
            df = df.iloc[::-1].reset_index(drop=True)
            return df
        else:
            raise Exception(f"Failed to fetch data: {response['retMsg']}")

    def calculate_rsi(self, closes, period=RSI_PERIOD):
        """Calculate RSI"""
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gains = np.convolve(gains, np.ones(period)/period, mode='valid')
        avg_losses = np.convolve(losses, np.ones(period)/period, mode='valid')

        rs = avg_gains / (avg_losses + 1e-10)
        rsi = 100 - (100 / (1 + rs))

        # Pad with NaN for the first `period` values
        rsi_full = np.empty(len(closes))
        rsi_full[:] = np.nan
        rsi_full[period:] = rsi
        return rsi_full

    def run_backtest(self, df):
        """Run RSI strategy backtest"""
        print("\n🧪 Running backtest...")

        df['rsi'] = self.calculate_rsi(df['close'].values)
        df['signal'] = 0

        for i in range(RSI_PERIOD + 1, len(df)):
            price = df['close'].iloc[i]
            rsi = df['rsi'].iloc[i]

            # Skip if RSI is NaN
            if np.isnan(rsi):
                continue

            if self.position is None:
                # No position - check for entry
                if rsi < RSI_OVERSOLD:
                    # Buy signal
                    self.position = {
                        'side': 'long',
                        'entry_price': price,
                        'entry_time': i
                    }
                    df.at[i, 'signal'] = 1

                elif rsi > RSI_OVERBOUGHT:
                    # Sell signal (short)
                    self.position = {
                        'side': 'short',
                        'entry_price': price,
                        'entry_time': i
                    }
                    df.at[i, 'signal'] = -1

            else:
                # Have position - check for exit
                exit = False
                pnl = 0

                if self.position['side'] == 'long':
                    pnl = (price - self.position['entry_price']) / self.position['entry_price']
                    # Exit if RSI recovers or profitable
                    if rsi > 50 or pnl > 0.04 or pnl < -0.02:
                        exit = True
                else:
                    pnl = (self.position['entry_price'] - price) / self.position['entry_price']
                    if rsi < 50 or pnl > 0.04 or pnl < -0.02:
                        exit = True

                if exit:
                    self.trades.append({
                        'side': self.position['side'],
                        'entry': self.position['entry_price'],
                        'exit': price,
                        'pnl': pnl,
                        'duration': i - self.position['entry_time']
                    })
                    self.balance *= (1 + pnl)
                    self.position = None

        return df

    def print_results(self):
        """Print backtest statistics"""
        print("\n" + "=" * 50)
        print("BACKTEST RESULTS")
        print("=" * 50)

        print(f"\nStrategy: RSI Mean Reversion")
        print(f"Period: {RSI_PERIOD}")
        print(f"Overbought: {RSI_OVERBOUGHT}")
        print(f"Oversold: {RSI_OVERSOLD}")
        print(f"Symbol: {SYMBOL}")
        print(f"Timeframe: {TIMEFRAME}m")

        print(f"\n📊 Performance:")
        print(f"Initial Balance: ${self.initial_balance:,.2f}")
        print(f"Final Balance: ${self.balance:,.2f}")
        print(f"Total Return: {((self.balance/self.initial_balance)-1)*100:.2f}%")

        if len(self.trades) > 0:
            wins = sum(1 for t in self.trades if t['pnl'] > 0)
            losses = len(self.trades) - wins
            win_rate = (wins / len(self.trades)) * 100

            print(f"\n📈 Trades:")
            print(f"Total Trades: {len(self.trades)}")
            print(f"Wins: {wins}")
            print(f"Losses: {losses}")
            print(f"Win Rate: {win_rate:.1f}%")

            avg_win = np.mean([t['pnl'] for t in self.trades if t['pnl'] > 0]) * 100 if wins > 0 else 0
            avg_loss = np.mean([t['pnl'] for t in self.trades if t['pnl'] < 0]) * 100 if losses > 0 else 0
            print(f"Avg Win: {avg_win:.2f}%")
            print(f"Avg Loss: {avg_loss:.2f}%")

            profit_factor = abs(sum(t['pnl'] for t in self.trades if t['pnl'] > 0) /
                               sum(t['pnl'] for t in self.trades if t['pnl'] < 0)) if losses > 0 else float('inf')
            print(f"Profit Factor: {profit_factor:.2f}")

            print(f"\n🔍 Recent Trades:")
            for t in self.trades[-5:]:
                emoji = "✅" if t['pnl'] > 0 else "❌"
                print(f"  {emoji} {t['side'].upper():5} | Entry: ${t['entry']:,.2f} | "
                      f"Exit: ${t['exit']:,.2f} | PnL: {t['pnl']*100:+.2f}%")
        else:
            print("\nNo trades generated in this period.")

    def plot_results(self, df):
        """Plot price and RSI with signals"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10),
                                            gridspec_kw={'height_ratios': [3, 1]})

            # Price chart
            ax1.plot(df.index, df['close'], label='Price', color='black', alpha=0.7)

            # Signals
            buy_signals = df[df['signal'] == 1]
            sell_signals = df[df['signal'] == -1]

            ax1.scatter(buy_signals.index, buy_signals['close'],
                       color='green', marker='^', s=100, label='Buy Signal', zorder=5)
            ax1.scatter(sell_signals.index, sell_signals['close'],
                       color='red', marker='v', s=100, label='Sell Signal', zorder=5)

            ax1.set_title(f'{SYMBOL} RSI Strategy Backtest')
            ax1.set_ylabel('Price (USDT)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # RSI chart
            ax2.plot(df.index, df['rsi'], label='RSI', color='purple')
            ax2.axhline(y=RSI_OVERBOUGHT, color='red', linestyle='--', label=f'Overbought ({RSI_OVERBOUGHT})')
            ax2.axhline(y=RSI_OVERSOLD, color='green', linestyle='--', label=f'Oversold ({RSI_OVERSOLD})')
            ax2.axhline(y=50, color='gray', linestyle='-', alpha=0.5)
            ax2.fill_between(df.index, RSI_OVERSOLD, RSI_OVERBOUGHT, alpha=0.1, color='gray')

            ax2.set_ylabel('RSI')
            ax2.set_xlabel('Candle')
            ax2.set_ylim(0, 100)
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig('backtest_results.png')
            print("\n📊 Chart saved as 'backtest_results.png'")
            plt.show()
        except Exception as e:
            print(f"\n⚠️ Could not generate chart: {e}")
            print("Install matplotlib to see visual results: pip install matplotlib")

if __name__ == "__main__":
    bt = RSI_backtest()
    try:
        df = bt.get_historical_data(days=30)
        df = bt.run_backtest(df)
        bt.print_results()
        bt.plot_results(df)
    except Exception as e:
        print(f"❌ Error: {e}")
