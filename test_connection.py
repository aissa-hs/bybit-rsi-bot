#!/usr/bin/env python3
"""
Test script to verify Bybit API connection and bot setup
Run this before starting the live bot!
"""

from pybit.unified_trading import HTTP
from config import API_KEY, API_SECRET, SYMBOLS, TESTNET

SYMBOL = SYMBOLS[0] if SYMBOLS else "BTCUSDT"

def test_connection():
    print("=" * 50)
    print("Bybit RSI Bot - Connection Test")
    print("=" * 50)
    print(f"Environment: {'TESTNET' if TESTNET else 'LIVE'}")
    print(f"Symbol: {SYMBOL}")
    print()

    try:
        # Initialize client
        print("🔌 Connecting to Bybit...")
        session = HTTP(
            testnet=TESTNET,
            api_key=API_KEY,
            api_secret=API_SECRET,
        )
        print("✅ Connected successfully!\n")

        # Test 1: Get server time
        print("⏱️  Testing server time...")
        response = session.get_server_time()
        if response['retCode'] == 0:
            print(f"✅ Server time: {response['result']['timeSecond']}")
        else:
            print(f"❌ Failed: {response['retMsg']}")

        # Test 2: Get account info
        print("\n💰 Testing account info...")
        response = session.get_wallet_balance(
            accountType="UNIFIED",
            coin="USDT"
        )
        if response['retCode'] == 0:
            balance_data = response['result']['list'][0]['coin'][0]
            print(f"✅ Account accessible!")
            print(f"   Wallet Balance: {balance_data['walletBalance']} USDT")
            print(f"   Available: {balance_data['availableToWithdraw']} USDT")
        else:
            print(f"❌ Failed: {response['retMsg']}")

        # Test 3: Get ticker info
        print(f"\n📊 Testing market data for {SYMBOL}...")
        response = session.get_tickers(
            category="linear",
            symbol=SYMBOL
        )
        if response['retCode'] == 0:
            ticker = response['result']['list'][0]
            print(f"✅ Market data retrieved!")
            print(f"   Current Price: {ticker['lastPrice']} USDT")
            print(f"   24h Change: {ticker['price24hPcnt']}")
            print(f"   24h Volume: {ticker['turnover24h']}")
        else:
            print(f"❌ Failed: {response['retMsg']}")

        # Test 4: Get klines
        print(f"\n📈 Testing kline data...")
        response = session.get_kline(
            category="linear",
            symbol=SYMBOL,
            interval="15",
            limit=20
        )
        if response['retCode'] == 0:
            klines = response['result']['list']
            print(f"✅ Kline data retrieved!")
            print(f"   Candles fetched: {len(klines)}")
            print(f"   Latest close: {klines[0][4]} USDT")
        else:
            print(f"❌ Failed: {response['retMsg']}")

        # Test 5: Get positions
        print(f"\n📍 Testing position data...")
        response = session.get_positions(
            category="linear",
            symbol=SYMBOL
        )
        if response['retCode'] == 0:
            positions = response['result']['list']
            print(f"✅ Position data retrieved!")
            if any(float(p['size']) > 0 for p in positions):
                print(f"   ⚠️  You have open positions on {SYMBOL}")
            else:
                print(f"   No open positions on {SYMBOL}")
        else:
            print(f"❌ Failed: {response['retMsg']}")

        print("\n" + "=" * 50)
        print("All tests completed! Your bot should be ready to run.")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Review your config.py settings")
        print("2. Start with TESTNET = True for testing")
        print("3. Run: python bybit_rsi_bot.py")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPossible issues:")
        print("- Invalid API credentials")
        print("- API key doesn't have Unified Trading permissions")
        print("- Network connectivity issues")
        print("- Using wrong environment (testnet vs live)")

if __name__ == "__main__":
    test_connection()
