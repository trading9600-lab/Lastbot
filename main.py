import ccxt
import pandas as pd
import requests
import time
import os
from datetime import datetime, timezone

# ===============================
# 🤖 BOT SOURCE (ADDED)
# ===============================
BOT_SOURCE = "GITHUB_ACTIONS"

# ===============================
# 🔐 TELEGRAM DETAILS (HARDCODED AS YOU ASKED)
# ===============================
TOKEN = "8364584748:AAFeym3et4zJwmdKRxYtP3ieIKV8FuPWdQ8"
CHAT_ID = "@Tradecocom"

# ===============================
# SETTINGS (UNCHANGED)
# ===============================
PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]

EMA_FAST = 20
EMA_SLOW = 50
SWING_LOOKBACK = 15

# ===============================
# ✅ MEXC EXCHANGE (GITHUB SAFE)
# ===============================
exchange = ccxt.mexc({
    "enableRateLimit": True,
})

last_alert = {}

# ===============================
# TELEGRAM MESSAGE
# ===============================
def send_alert(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data, timeout=10)

# ===============================
# FETCH DATA
# ===============================
def get_data(symbol, timeframe):
    candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
    df = pd.DataFrame(
        candles,
        columns=["time", "open", "high", "low", "close", "volume"]
    )
    return df

# ===============================
# SIGNAL CHECK (UNCHANGED LOGIC)
# ===============================
def check_signal(symbol, timeframe):
    df = get_data(symbol, timeframe)

    df["ema20"] = df["close"].ewm(span=EMA_FAST).mean()
    df["ema50"] = df["close"].ewm(span=EMA_SLOW).mean()

    prev_fast = df["ema20"].iloc[-2]
    prev_slow = df["ema50"].iloc[-2]
    curr_fast = df["ema20"].iloc[-1]
    curr_slow = df["ema50"].iloc[-1]

    price = df["close"].iloc[-1]

    swing_high = df["high"].iloc[-SWING_LOOKBACK:].max()
    swing_low = df["low"].iloc[-SWING_LOOKBACK:].min()

    signal = None

    if prev_fast < prev_slow and curr_fast > curr_slow:
        signal = "🟢 BUY | EMA 20 Cross Above EMA 50"

    elif prev_fast > prev_slow and curr_fast < curr_slow:
        signal = "🔴 SELL | EMA 20 Cross Below EMA 50"

    elif price > swing_high:
        signal = "🚀 BULLISH BREAKOUT | Swing High Broken"

    elif price < swing_low:
        signal = "🩸 BEARISH BREAKDOWN | Swing Low Broken"

    if signal:
        key = f"{symbol}_{timeframe}_{signal}"
        candle_time = df["time"].iloc[-1]

        if last_alert.get(key) != candle_time:
            last_alert[key] = candle_time

            message = (
                f"{signal}\n"
                f"🤖 Source: {BOT_SOURCE}\n\n"
                f"📊 Pair: {symbol}\n"
                f"⏱ Timeframe: {timeframe}\n"
                f"💰 Price: {price}\n"
                f"🕒 UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
            )

            send_alert(message)
            return True

    return False

# ===============================
# START MESSAGE
# ===============================
send_alert(
    "✅ Crypto Signal Bot started successfully (MEXC)\n"
    f"🤖 Source: {BOT_SOURCE}"
)

# ===============================
# MAIN LOOP
# ===============================
while True:
    try:
        for pair in PAIRS:
            for tf in TIMEFRAMES:
                check_signal(pair, tf)

        time.sleep(300)  # 5 minutes

    except Exception as e:
        send_alert(
            f"⚠️ Bot error: {e}\n"
            f"🤖 Source: {BOT_SOURCE}"
        )
        time.sleep(60)
        
