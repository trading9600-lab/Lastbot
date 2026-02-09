import ccxt
import pandas as pd
import requests
import os
from datetime import datetime, timezone

# ===============================
# 🤖 BOT SOURCE
# ===============================
BOT_SOURCE = "GITHUB_ACTIONS"

# ===============================
# 🔐 TELEGRAM (USE SECRETS)
# ===============================
TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["TG_CHAT_ID"]

# ===============================
# SETTINGS
# ===============================
PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]

EMA_FAST = 20
EMA_SLOW = 50
SWING_LOOKBACK = 15

# ===============================
# EXCHANGE
# ===============================
exchange = ccxt.mexc({"enableRateLimit": True})

# ===============================
# TELEGRAM SEND (SAFE)
# ===============================
def send_alert(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

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
# SIGNAL CHECK
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
        signal = "🚀 BULLISH BREAKOUT"
    elif price < swing_low:
        signal = "🩸 BEARISH BREAKDOWN"

    if signal:
        message = (
            f"{signal}\n"
            f"🤖 Source: {BOT_SOURCE}\n\n"
            f"📊 Pair: {symbol}\n"
            f"⏱ Timeframe: {timeframe}\n"
            f"💰 Price: {price}\n"
            f"🕒 UTC: {datetime.now(timezone.utc)}"
        )
        send_alert(message)

# ===============================
# START MESSAGE (ONCE PER RUN)
# ===============================
send_alert("✅ Crypto Signal Bot started successfully")

# ===============================
# RUN ONCE (IMPORTANT)
# ===============================
for pair in PAIRS:
    for tf in TIMEFRAMES:
        check_signal(pair, tf)
