# Bybit RSI Trading Bot

An automated trading bot for Bybit Futures that uses the RSI (Relative Strength Index) indicator to generate buy and sell signals on BTC/USDT perpetual contracts.

## Strategy

- **Long Entry**: When RSI < 30 (oversold)
- **Short Entry**: When RSI > 70 (overbought)
- **Exit**: When RSI returns to neutral (~50) or stop loss/take profit triggered

## Features

- RSI-based mean reversion strategy
- Automatic stop loss and take profit
- Position size management
- Leverage configuration
- Testnet support for safe testing
- Comprehensive logging

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Get Bybit API keys:**
   - Go to: https://www.bybit.com/app/user/api-management
   - Create new API keys
   - Enable **Unified Trading** permissions
   - For testing, use Testnet: https://testnet.bybit.com

3. **Configure the bot:**
   - Edit `config.py` with your API keys and settings

4. **Test first!**
   - Set `TESTNET = True` in config.py
   - Run the bot to verify it works
   - Only then switch to live trading

## Configuration

Edit `config.py`:

```python
# API Keys (required)
API_KEY = "your_api_key_here"
API_SECRET = "your_api_secret_here"

# Trading Settings
SYMBOL = "BTCUSDT"        # Trading pair
TIMEFRAME = "15"          # Candle timeframe in minutes
LEVERAGE = 5              # Futures leverage (1-125)

# RSI Settings
RSI_PERIOD = 14           # RSI calculation period
RSI_OVERBOUGHT = 70       # Sell/Short threshold
RSI_OVERSOLD = 30         # Buy/Long threshold

# Risk Management
POSITION_SIZE_USDT = 100  # USDT amount per trade
STOP_LOSS_PERCENT = 2.0   # Stop loss %
TAKE_PROFIT_PERCENT = 4.0 # Take profit %

# Trading Mode
TESTNET = True            # True = testnet, False = live trading
```

## Usage

Run the bot:
```bash
python bybit_rsi_bot.py
```

The bot will:
1. Check your account balance
2. Monitor RSI on 15m candles
3. Open positions based on RSI signals
4. Log all activity to console and `trading_bot.log`

## ⚠️ Risk Warning

**Trading cryptocurrencies carries significant risk:**
- Futures trading with leverage can result in total loss of funds
- This bot is provided for educational purposes
- Always test on testnet first
- Never risk more than you can afford to lose
- Past performance does not guarantee future results

## Files

- `bybit_rsi_bot.py` - Main bot code
- `config.py` - Configuration settings
- `requirements.txt` - Python dependencies
- `trading_bot.log` - Trading activity log

## Customization

### Adjust RSI thresholds
```python
RSI_OVERSOLD = 25    # More conservative long entries
RSI_OVERBOUGHT = 75  # More conservative short entries
```

### Change timeframe
```python
TIMEFRAME = "60"     # 1 hour candles
```

### Modify position sizing
```python
POSITION_SIZE_USDT = 50  # Smaller positions
```

## Troubleshooting

**"Invalid API key" error:**
- Verify API keys are correct
- Check that Unified Trading is enabled
- Ensure you're using the right environment (testnet vs live)

**"Insufficient margin" error:**
- Reduce `POSITION_SIZE_USDT`
- Lower `LEVERAGE`
- Check your USDT balance

**Bot not placing orders:**
- Check `trading_bot.log` for errors
- Verify RSI values are crossing thresholds
- Ensure you have sufficient balance

## License

Use at your own risk. Not financial advice.
