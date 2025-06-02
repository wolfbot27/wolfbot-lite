from binance.client import Client
import pandas as pd

client = Client()

def get_recent_closes(symbol, interval='1m', limit=10):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    closes = [float(k[4]) for k in klines]
    return closes

def get_trading_confidence(symbol, threshold=0.0003):
    """
    Son 10 kapanışa göre fiyatın oynaklığına ve yönüne bakar.
    Yalnızca küçük oynaklık değil, aynı yönde ilerleme varsa güven verir.
    """
    closes = get_recent_closes(symbol)
    if len(closes) < 2:
        return False

    # Yönlü değişim hesaplama (pozitif ise yukarı trend)
    direction_count = 0
    for i in range(1, len(closes)):
        if closes[i] > closes[i-1]:
            direction_count += 1
        elif closes[i] < closes[i-1]:
            direction_count -= 1

    # Oynaklık ölçümü
    diffs = [abs(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
    avg_diff = sum(diffs) / len(diffs)

    # Güven: hem oynaklık hem yönsel netlik olmalı
    is_trending = avg_diff >= threshold and abs(direction_count) >= 3
    return is_trending
