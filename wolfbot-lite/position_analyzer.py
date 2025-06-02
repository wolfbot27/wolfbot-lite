from logger import log
import talib as ta
import numpy as np
from binance.client import Client
from config import API_KEY, API_SECRET
from risk_trend_analyzer import get_trading_confidence  # ✅ Eklendi

client = Client(API_KEY, API_SECRET)

def evaluate_position(symbol, entry_price, current_price, position_side):
    try:
        # Fiyat farkı
        fark_orani = (current_price - entry_price) / entry_price if position_side == "LONG" else (entry_price - current_price) / entry_price
        log.info(f"{symbol} ➜ Pozisyon Analizi ({position_side}) ➜ Fark: %{round(fark_orani * 100, 3)}")

        # Teknik göstergeler
        klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=50)
        closes = np.array([float(k[4]) for k in klines])
        volumes = np.array([float(k[5]) for k in klines])

        rsi = ta.RSI(closes, timeperiod=14)[-1]
        macd, signal, _ = ta.MACD(closes, fastperiod=8, slowperiod=21, signalperiod=5)
        macd_histogram = macd[-1] - signal[-1]
        vol_ma = ta.SMA(volumes, timeperiod=20)[-1]

        # ✅ %1 kâr ve güçlü trend → TP/SL güncelle
        if fark_orani >= 0.01 and get_trading_confidence(symbol, threshold=0.0005):
            log.info(f"{symbol} ➜ %1 kâr ve güçlü trend ➜ TP/SL güncelle önerisi.")
            return "adjust_tp_sl"

        # LONG pozisyon için çıkış sinyali
        if position_side == "LONG" and rsi > 74 and macd_histogram < 0 and volumes[-1] < vol_ma:
            log.warning(f"{symbol} ➜ Teknik olarak LONG pozisyon kapatma sinyali oluştu.")
            return "close"

        # SHORT pozisyon için çıkış sinyali
        if position_side == "SHORT" and rsi < 26 and macd_histogram > 0 and volumes[-1] < vol_ma:
            log.warning(f"{symbol} ➜ Teknik olarak SHORT pozisyon kapatma sinyali oluştu.")
            return "close"

        # ❌ %1.5 zarar varsa kapat
        if fark_orani <= -0.015:
            log.warning(f"{symbol} ➜ %1.5 zarar sınırına ulaşıldı ➜ POZİSYON KAPAT.")
            return "close"

        # ✅ %1.5 kâr → trail başlasın
        if fark_orani >= 0.015:
            log.info(f"{symbol} ➜ TP seviyesi olan %1.5'e ulaşıldı.")
            return "trail"

        return "keep"

    except Exception as e:
        log.error(f"{symbol} analiz hatası: {e}")
        return "keep"

