import ccxt
import pandas as pd
import requests
import time
from datetime import datetime, timezone

# ===============================
# 🤖 BOT SOURCE
# ===============================
BOT_SOURCE = "GITHUB_ACTIONS"

# ===============================
# 🔐 TELEGRAM
# ===============================
TOKEN = "8364584748:AAFeym3et4zJwmdKRxYtP3ieIKV8FuPWdQ8"
CHAT_ID = "@Tradecocom"

# ===============================
# ⚙️ SETTINGS
# ===============================
PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]

EMA_FAST = 20
EMA_SLOW = 50

SCAN_INTERVAL = 3600     # 1 hour
MAX_RUNTIME = 3700       # GitHub safe runtime
COOLDOWN = 600           # 10 minutes cooldown

# ===============================
# 🔁 EXCHANGE
# ===============================
exchange = ccxt.mexc({"enableRateLimit": True})

# ===============================
# 🧠 MEMORY (NO DUPLICATES)
# ===============================
last_signal_time = {}

# ===============================
# 📩 TELEGRAM
# ===============================
def send_alert(text):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text}
    )

# ===============================
# 📊 DATA
# ===============================
def fetch_data(symbol, timeframe):
    candles = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
    return pd.DataFrame(
        candles,
        columns=["time", "open", "high", "low", "close", "volume"]
    )

# ===============================
# 🚀 EMA SIGNAL (CLOSED CANDLE)
# ===============================
def check_signal(symbol, timeframe):
    df = fetch_data(symbol, timeframe)

    df["ema_fast"] = df["close"].ewm(span=EMA_FAST).mean()
    df["ema_slow"] = df["close"].ewm(span=EMA_SLOW).mean()

    prev = df.iloc[-3]
    curr = df.iloc[-2]  # ✅ last CLOSED candle

    key = f"{symbol}_{timeframe}"
    now = time.time()

    if key in last_signal_time and now - last_signal_time[key] < COOLDOWN:
        return

    if prev.ema_fast < prev.ema_slow and curr.ema_fast > curr.ema_slow:
        signal = "🟢 BUY | EMA 20 CROSS ABOVE EMA 50"
    elif prev.ema_fast > prev.ema_slow and curr.ema_fast < curr.ema_slow:
        signal = "🔴 SELL | EMA 20 CROSS BELOW EMA 50"
    else:
        return

    last_signal_time[key] = now

    send_alert(
        f"{signal}\n"
        f"🤖 Source: {BOT_SOURCE}\n\n"
        f"📊 Pair: {symbol}\n"
        f"⏱ Timeframe: {timeframe}\n"
        f"💰 Close: {curr.close}\n"
        f"🕒 UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
    )

# ===============================
# ▶️ MAIN (HOURLY SCAN)
# ===============================
def main():
    send_alert(
        "🔍 Market Scan Started\n"
        "⏱ Interval: 1 Hour\n"
        f"🤖 Source: {BOT_SOURCE}"
    )

    start_time = time.time()

    while time.time() - start_time < MAX_RUNTIME:
        for pair in PAIRS:
            for tf in TIMEFRAMES:
                check_signal(pair, tf)

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
