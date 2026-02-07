import ccxt
import pandas as pd
import requests
import json
import os
from datetime import datetime, timezone

# ===============================
# TELEGRAM (FROM GITHUB SECRETS)
# ===============================
TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# ===============================
# SETTINGS
# ===============================
PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]

EMA_FAST = 20
EMA_SLOW = 50
SWING_LOOKBACK = 15
STATE_FILE = "state.json"

# ===============================
# EXCHANGE
# ===============================
exchange = ccxt.bybit({
    "enableRateLimit": True,
    "options": {"defaultType": "spot"}
})

# ===============================
# TELEGRAM
# ===============================
def send_alert(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": text},
        timeout=10
    )

# ===============================
# STATE
# ===============================
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ===============================
# DATA
# ===============================
def get_data(symbol, timeframe):
    candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
    return pd.DataFrame(
        candles,
        columns=["time", "open", "high", "low", "close", "volume"]
    )

# ===============================
# SIGNAL LOGIC
# ===============================
def check_signal(symbol, timeframe, state):
    df = get_data(symbol, timeframe)

    df["ema20"] = df["close"].ewm(span=EMA_FAST).mean()
    df["ema50"] = df["close"].ewm(span=EMA_SLOW).mean()

    prev_fast, prev_slow = df["ema20"].iloc[-2], df["ema50"].iloc[-2]
    curr_fast, curr_slow = df["ema20"].iloc[-1], df["ema50"].iloc[-1]

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

    if not signal:
        return

    candle_time = str(df["time"].iloc[-1])
    key = f"{symbol}_{timeframe}_{signal}"

    if state.get(key) == candle_time:
        return  # prevent duplicate

    state[key] = candle_time

    send_alert(
        f"{signal}\n\n"
        f"📊 Pair: {symbol}\n"
        f"⏱ Timeframe: {timeframe}\n"
        f"💰 Price: {price}\n"
        f"🕒 UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
    )

# ===============================
# MAIN
# ===============================
def main():
    # 🔔 BOT START MESSAGE
    send_alert(
        "🚀 TradingCo Bot Started\n\n"
        f"🕒 UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n"
        "✅ GitHub Actions is running"
    )

    state = load_state()

    for pair in PAIRS:
        for tf in TIMEFRAMES:
            try:
                check_signal(pair, tf, state)
            except Exception as e:
                print(f"⚠️ {pair} {tf} error:", e)

    save_state(state)

if __name__ == "__main__":
    main()
  
