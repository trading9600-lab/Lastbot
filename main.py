import ccxt
import pandas as pd
import requests
import time
from datetime import datetime, timezone

# ===============================
# TELEGRAM (HARDCODED – AS REQUESTED)
# ===============================
TOKEN = "8364584748:AAFeym3et4zJwmdKRxYtP3ieIKV8FuPWdQ8"
CHAT_ID = "@Tradecocom"

# ===============================
# SETTINGS
# ===============================
PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]

EMA_FAST = 20
EMA_SLOW = 50
SWING_LOOKBACK = 15

# ===============================
# BINANCE
# ===============================
exchange = ccxt.binance({
    "enableRateLimit": True,
    "options": {"defaultType": "spot"}
})

last_alert = {}

# ===============================
# TELEGRAM FUNCTION
# ===============================
def send_alert(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=payload, timeout=10)

# ===============================
# FETCH MARKET DATA
# ===============================
def get_data(symbol, timeframe):
    candles = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
    return pd.DataFrame(
        candles,
        columns=["time", "open", "high", "low", "close", "volume"]
    )

# ===============================
# SIGNAL LOGIC
# ===============================
def check_signal(symbol, timeframe):
    df = get_data(symbol, timeframe)

    df["ema20"] = df["close"].ewm(span=EMA_FAST).mean()
    df["ema50"] = df["close"].ewm(span=EMA_SLOW).mean()

    prev_fast, curr_fast = df["ema20"].iloc[-2], df["ema20"].iloc[-1]
    prev_slow, curr_slow = df["ema50"].iloc[-2], df["ema50"].iloc[-1]

    price = df["close"].iloc[-1]
    swing_high = df["high"].iloc[-SWING_LOOKBACK:].max()
    swing_low = df["low"].iloc[-SWING_LOOKBACK:].min()

    signal = None

    if prev_fast < prev_slow and curr_fast > curr_slow:
        signal = "🟢 BUY | EMA20 crossed ABOVE EMA50"
    elif prev_fast > prev_slow and curr_fast < curr_slow:
        signal = "🔴 SELL | EMA20 crossed BELOW EMA50"
    elif price > swing_high:
        signal = "🚀 BREAKOUT"
    elif price < swing_low:
        signal = "🩸 BREAKDOWN"

    if signal:
        key = f"{symbol}_{timeframe}_{signal}"
        candle_time = df["time"].iloc[-1]

        if last_alert.get(key) != candle_time:
            last_alert[key] = candle_time
            send_alert(
                f"{signal}\n\n"
                f"📊 Pair: {symbol}\n"
                f"⏱ Timeframe: {timeframe}\n"
                f"💰 Price: {price}\n"
                f"🕒 {datetime.now(timezone.utc)}"
            )

# ===============================
# START MESSAGE
# ===============================
send_alert("✅ Crypto Signal Bot started successfully")

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
        send_alert(f"⚠️ Bot error: {e}")
        time.sleep(60)
        
