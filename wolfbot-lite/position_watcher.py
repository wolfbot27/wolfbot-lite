import time
from logger import log
from binance.client import Client
from config import API_KEY, API_SECRET
from position_analyzer import evaluate_position
from market_memory import get_major_market_snapshot  # <-- Yeni entegre

last_tp_update = {}  # {symbol: fiyat}
KONTROL_ARALIGI = 2  # saniye
client = Client(API_KEY, API_SECRET)

def get_current_price(symbol):
    try:
        price = float(client.futures_mark_price(symbol=symbol)['markPrice'])
        return price
    except Exception as e:
        log.error(f"{symbol} fiyat alınamadı: {e}")
        return None

def kapat_pozisyon(symbol, position_side, fark):
    try:
        log.info(f"{symbol} ➜ {position_side} pozisyon KAPATILIYOR...")
        client.futures_create_order(
            symbol=symbol,
            side="SELL" if position_side == "LONG" else "BUY",
            type="MARKET",
            quantity=get_position_quantity(symbol, position_side),
            positionSide=position_side
        )
        log.info(f"{symbol} ➜ {position_side} pozisyon KAPANDI.")

        # 📦 Kapanan pozisyonun sonucu market_memory'ye gönderiliyor
        if fark >= 0:
            get_major_market_snapshot(result="win")
        else:
            get_major_market_snapshot(result="loss")

    except Exception as e:
        log.error(f"{symbol} pozisyon kapatılamadı: {e}")

def get_position_quantity(symbol, position_side):
    try:
        positions = client.futures_position_information(symbol=symbol)
        for pos in positions:
            if pos["positionSide"] == position_side and float(pos["positionAmt"]) != 0:
                return abs(float(pos["positionAmt"]))
        return 0
    except Exception as e:
        log.error(f"{symbol} pozisyon miktarı alınamadı: {e}")
        return 0

def get_active_positions():
    try:
        positions = client.futures_position_information()
        aktifler = []
        for pos in positions:
            amount = float(pos['positionAmt'])
            if amount != 0:
                aktifler.append({
                    'symbol': pos['symbol'],
                    'entryPrice': float(pos['entryPrice']),
                    'positionAmt': amount,
                    'positionSide': pos['positionSide']
                })
        return aktifler
    except Exception as e:
        log.error(f"Açık pozisyonlar alınamadı: {e}")
        return []

def guncelle_tp_sl(symbol, position_side, current_price):
    try:
        opposite_side = "SELL" if position_side == "LONG" else "BUY"
        if position_side == "LONG":
            new_tp = round(current_price * 1.03, 4)
            new_sl = round(current_price * 0.97, 4)
        else:
            new_tp = round(current_price * 0.97, 4)
            new_sl = round(current_price * 1.03, 4)

        client.futures_cancel_all_open_orders(symbol=symbol)

        client.futures_create_order(
            symbol=symbol,
            side=opposite_side,
            type="TAKE_PROFIT_MARKET",
            stopPrice=new_tp,
            closePosition=True,
            positionSide=position_side,
            timeInForce="GTC"
        )

        client.futures_create_order(
            symbol=symbol,
            side=opposite_side,
            type="STOP_MARKET",
            stopPrice=new_sl,
            closePosition=True,
            positionSide=position_side,
            timeInForce="GTC"
        )

        log.info(f"{symbol} ➜ Yeni TP: {new_tp}, Yeni SL: {new_sl} ➜ Emirler güncellendi.")
    except Exception as e:
        log.error(f"{symbol} ➜ TP/SL güncelleme hatası: {e}")

def kontrol_et():
    while True:
        aktifler = get_active_positions()
        for poz in aktifler:
            try:
                symbol = poz['symbol']
                entry = poz['entryPrice']
                side = poz['positionSide']
                amount = poz['positionAmt']
                current = get_current_price(symbol)

                if current is None or entry == 0:
                    continue

                fark_orani = (current - entry) / entry if side == "LONG" else (entry - current) / entry
                log.info(f"{symbol} ➜ {side} ➜ Kar/Zarar: %{round(fark_orani * 100, 3)}")

                karar = evaluate_position(symbol, entry, current, side)

                if karar == "close":
                    log.info(f"{symbol} ➜ Akıllı analiz sonucu: POZİSYON KAPATILACAK.")
                    kapat_pozisyon(symbol, side, fark_orani)

                elif karar == "adjust_tp_sl":
                    son_fiyat = last_tp_update.get(symbol, entry)
                    fark = (current - son_fiyat) / son_fiyat * 100

                    if fark >= 1.0:
                        log.info(f"{symbol} ➜ Fiyat farkı: %{fark:.2f} ➜ TP/SL GÜNCELLENİYOR.")
                        guncelle_tp_sl(symbol, side, current)
                        last_tp_update[symbol] = current
                    else:
                        log.info(f"{symbol} ➜ Fiyat farkı: %{fark:.2f} ➜ %1 üstü kar yok, TP/SL sabit.")

                elif karar == "trail":
                    son_fiyat = last_tp_update.get(symbol, entry)
                    gerileme = (son_fiyat - current) / son_fiyat * 100 if side == "LONG" else (current - son_fiyat) / son_fiyat * 100

                    if gerileme >= 0.5:
                        log.warning(f"{symbol} ➜ %1.5 kâr sonrası %0.5 geri çekilme ➜ POZİSYON KAPANIYOR.")
                        kapat_pozisyon(symbol, side, fark_orani)
                    else:
                        last_tp_update[symbol] = current
                        log.info(f"{symbol} ➜ Trailing aktif ➜ Henüz %0.5 geri çekilme yok.")

                else:
                    log.info(f"{symbol} ➜ Akıllı analiz sonucu: Pozisyon DEVAM.")
            except Exception as e:
                log.error(f"{symbol} analiz sırasında hata: {e}")

        time.sleep(KONTROL_ARALIGI)

if __name__ == "__main__":
    log.info("🟢 Pozisyon Takibi Başlatıldı (TP/SL Dinamik)...")
    kontrol_et()
