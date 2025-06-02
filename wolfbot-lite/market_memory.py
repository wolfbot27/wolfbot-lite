from logger import log
import time
import os
import json
from datetime import datetime, timedelta
from binance.client import Client
from config import API_KEY, API_SECRET

client = Client(API_KEY, API_SECRET)

DATA_FOLDER = "market_data"
os.makedirs(DATA_FOLDER, exist_ok=True)

def get_coin_data(symbol):
    try:
        klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=50)
        closes = [float(kline[4]) for kline in klines]

        gains = [closes[i] - closes[i - 1] for i in range(1, len(closes)) if closes[i] > closes[i - 1]]
        losses = [closes[i - 1] - closes[i] for i in range(1, len(closes)) if closes[i] < closes[i - 1]]
        avg_gain = sum(gains) / 14 if gains else 0.0001
        avg_loss = sum(losses) / 14 if losses else 0.0001
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        ema20 = sum(closes[-20:]) / 20
        ema50 = sum(closes[-50:]) / 50

        def ema(values, period):
            alpha = 2 / (period + 1)
            ema_values = [values[0]]
            for price in values[1:]:
                ema_values.append((price - ema_values[-1]) * alpha + ema_values[-1])
            return ema_values

        macd_line = [a - b for a, b in zip(ema(closes, 12), ema(closes, 26))]
        signal_line = ema(macd_line, 9)
        macd_hist = macd_line[-1] - signal_line[-1]

        return {
            "symbol": symbol,
            "rsi": round(rsi, 2),
            "ema20": round(ema20, 4),
            "ema50": round(ema50, 4),
            "macd_hist": round(macd_hist, 5),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        log.warning(f"{symbol} veri alınamadı: {e}")
        return None

def save_snapshot(snapshot, result=None):
    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    file_path = os.path.join(DATA_FOLDER, f"{date_str}.json")

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        data = []

    snapshot_with_result = {
        "timestamp": snapshot[0].get("timestamp", now.isoformat()),
        "data": snapshot,
        "result": result
    }

    data.append(snapshot_with_result)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

def cleanup_old_data():
    today = datetime.utcnow().date()
    for fname in os.listdir(DATA_FOLDER):
        try:
            file_date = datetime.strptime(fname.replace(".json", ""), "%Y-%m-%d").date()
            if (today - file_date).days > 7:
                os.remove(os.path.join(DATA_FOLDER, fname))
        except Exception as e:
            log.warning(f"Eski dosya silinirken hata: {e}")

def get_major_market_snapshot(result=None):
    major_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
                     "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "LINKUSDT"]
    snapshot = []
    for symbol in major_symbols:
        data = get_coin_data(symbol)
        if data:
            snapshot.append(data)
        time.sleep(1)

    if snapshot:
        save_snapshot(snapshot, result=result)
        cleanup_old_data()

    return snapshot