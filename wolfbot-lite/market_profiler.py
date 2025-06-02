import os
import json
from datetime import datetime, timedelta

DATA_FOLDER = "market_data"

def load_market_data():
    snapshots = []
    today = datetime.utcnow().date()
    for i in range(7):
        date = today - timedelta(days=i)
        file_path = os.path.join(DATA_FOLDER, f"{date}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    snapshots.extend(data)
            except:
                continue
    return snapshots

def is_market_profitable():
    data = load_market_data()
    if not data:
        return True

    result_data = [x for x in data if x.get("result") in ["win", "loss"] and x.get("data")]
    if len(result_data) < 10:
        return True

    win_count = 0
    loss_count = 0

    for entry in result_data[-20:]:
        btc = next((coin for coin in entry["data"] if coin["symbol"] == "BTCUSDT"), None)
        if not btc:
            continue

        rsi = btc.get("rsi")
        macd = btc.get("macd_hist")
        ema_score = 1 if btc.get("ema20") > btc.get("ema50") else 0

        if rsi > 50 and macd > 0 and ema_score == 1:
            if entry["result"] == "win":
                win_count += 1
            else:
                loss_count += 1

    total = win_count + loss_count
    if total == 0:
        return True

    win_rate = win_count / total
    return win_rate >= 0.6