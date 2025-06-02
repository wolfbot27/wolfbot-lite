import time
from logger import log
import threading
from binance_api import BinanceFuturesClient
from risk_manager import RiskManager
from whale_tracker import is_whale_activity_detected
from market_detector import is_trending_market
from risk_trend_analyzer import get_trading_confidence
from position_watcher import kontrol_et as pozisyon_takibi
from top_movers import get_top_movers
from market_profiler import is_market_profitable
from market_memory import get_major_market_snapshot  # 🧠 15dk logger

symbol_list = get_top_movers(limit=20)

client = BinanceFuturesClient()
risk_manager = RiskManager()

log.info("WolfBotX Çoklu Coin İşlem Başlıyor...")

# 🔄 Pozisyon Takibi Thread
poz_takip_thread = threading.Thread(target=pozisyon_takibi)
poz_takip_thread.daemon = True
poz_takip_thread.start()

# 📦 15 Dakikalık Piyasa Snapshot Thread
def logger_loop():
    while True:
        try:
            get_major_market_snapshot(result=None)
            log.info("📦 Piyasa snapshot kaydedildi (15dk)")
        except Exception as e:
            log.warning(f"Market logger hatası: {e}")
        time.sleep(900)  # 15 dakika

market_logger_thread = threading.Thread(target=logger_loop)
market_logger_thread.daemon = True
market_logger_thread.start()

# 🧠 Ana İşlem Döngüsü
while True:
    if not is_market_profitable():
        log.info("📉 Piyasa geçmişe göre kazançlı değil. İzleme modunda.")
        time.sleep(15)
        continue

    for symbol in symbol_list:
        try:
            log.info(f"Kontrol ediliyor: {symbol}")
            signal = client.get_signal(symbol)
            whale_activity = is_whale_activity_detected(symbol)
            trending = is_trending_market(symbol)
            confident = get_trading_confidence(symbol)

            position_side = "LONG" if signal == "long" else "SHORT"

            if not client.has_open_position(symbol, "LONG") and not client.has_open_position(symbol, "SHORT"):
                open_orders = client.client.futures_get_open_orders(symbol=symbol)
                if open_orders:
                    client.client.futures_cancel_all_open_orders(symbol=symbol)
                    log.info(f"{symbol}: Pozisyon kapanmış ama emir kalmıştı, iptal edildi.")

            if signal and whale_activity and trending and confident:
                if not client.has_open_position(symbol, position_side):
                    usdt_amount = risk_manager.get_adjusted_amount(symbol, signal)
                    if usdt_amount:
                        client.open_position(symbol, signal, usdt_amount)
                        risk_manager.update_result(symbol, signal)
                    else:
                        log.error(f"{symbol}: Uygun miktar hesaplanamadı.")
                else:
                    log.info(f"{symbol}: Zaten açık {position_side} pozisyon var, işlem yapılmadı.")
            else:
                log.info(f"{symbol}: Sinyal yok, balina yok, piyasa yatay veya volatilite yetersiz.")
        except Exception as e:
            log.warning(f"{symbol} işlem döngüsünde hata: {e}")

        time.sleep(2)
