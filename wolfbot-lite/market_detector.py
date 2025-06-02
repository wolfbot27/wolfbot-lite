# market_detector.py

from binance.client import Client
import pandas as pd
import ta

client = Client()

def get_klines(symbol, interval='1m', limit=15):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    return df
def get_atr_value(symbol):
    df = get_klines(symbol)  # zaten tanımlı fonksiyon
    atr = ta.volatility.AverageTrueRange(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    ).average_true_range().iloc[-1]
    return atr
def is_trending_market(symbol, threshold=0.005):
    """
    True dönerse piyasa trendde, False dönerse yatay.
    """
    df = get_klines(symbol)
    atr = ta.volatility.AverageTrueRange(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14
    ).average_true_range().iloc[-1]

    price_range = df['close'].iloc[-1] - df['close'].iloc[-15]
    price_range = abs(price_range)

    # ATR 0 ise uyarı engellenir, piyasa yatay kabul edilir
    if atr == 0 or pd.isna(atr):
        return False

    if price_range / atr >= threshold:
        return True  # Piyasa trendde
    return False  # Piyasa yatay
