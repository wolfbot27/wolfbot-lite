from datetime import datetime
from logger import log
import numpy as np
import talib as ta
from binance.client import Client
from config import API_KEY, API_SECRET
from market_detector import is_trending_market, get_atr_value


class BinanceFuturesClient:
    def __init__(self):
        self.client = Client(API_KEY, API_SECRET)

    def calculate_macd_histogram(self, closes):
        import pandas as pd
        series = pd.Series(closes)
        ema12 = series.ewm(span=12, adjust=False).mean()
        ema26 = series.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        return histogram.iloc[-1]

    def get_confirmations(self, symbol):
        klines = self.client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=50)
        closes = np.array([float(k[4]) for k in klines])
        volumes = np.array([float(k[5]) for k in klines])

        rsi = ta.RSI(closes, timeperiod=14)[-1]
        rsi_fast_ema = ta.EMA(ta.RSI(closes, 3), timeperiod=3)[-1]
        rsi_slow_ema = ta.EMA(ta.RSI(closes, 8), timeperiod=8)[-1]
        rsi_momentum = rsi_fast_ema > rsi_slow_ema

        macd, signal, _ = ta.MACD(closes, fastperiod=8, slowperiod=21, signalperiod=5)
        macd_cross = macd[-1] > signal[-1]
        macd_positive = macd[-1] > 0

        obv = ta.OBV(closes, volumes)
        obv_direction = obv[-1] > obv[-2]

        vol_ma = ta.SMA(volumes, timeperiod=20)[-1]
        vol_explosion = volumes[-1] > 2.3 * vol_ma

        conditions = {
            "RSI < 35": rsi < 35,
            "RSI Momentum (fast > slow)": rsi_momentum,
            "MACD Cross (macd > signal)": macd_cross,
            "MACD Pozitif (macd > 0)": macd_positive,
            "OBV Yukarı": obv_direction,
            "Hacim Patlaması": vol_explosion
        }

        passed_count_long = sum(conditions.values())

        log.info(f"{symbol} ➜ 5 Onay Durumu:")
        for name, status in conditions.items():
            log.info(f" - {name}: {'✔️' if status else '❌'}")

        short_conditions = [
            rsi > 65,
            not rsi_momentum,
            not macd_cross,
            macd[-1] < 0,
            obv[-1] < obv[-2],
            volumes[-1] > 2.1 * vol_ma
        ]

        passed_count_short = sum(short_conditions)

        return {
            'long': passed_count_long >= 6,
            'short': passed_count_short >= 6
        }

    def get_signal(self, symbol):
        try:
            if not is_trending_market(symbol):
                log.info(f"{symbol} ➜ Piyasa yatay. Pozisyon açılmayacak.")
                return None

            confirmations = self.get_confirmations(symbol)

            if confirmations['long']:
                log.info(f"{symbol} ➜ En az 6 onay sağlandı ➜ LONG sinyali.")
                return "long"
            elif confirmations['short']:
                log.info(f"{symbol} ➜ En az 6 onay sağlandı ➜ SHORT sinyali.")
                return "short"
            else:
                log.info(f"{symbol} ➜ Gerekli onaylar yok ➜ POZİSYON AÇILMAYACAK.")
                return None
        except Exception as e:
            log.error(f"{symbol} ➜ Sinyal hesaplama hatası: {e}")
            return None

    def open_position(self, symbol, signal, usdt_amount):
        try:
            step_size = self.get_step_size(symbol)
            price = float(self.client.futures_symbol_ticker(symbol=symbol)['price'])
            quantity = round(usdt_amount / price, step_size)

            if quantity == 0:
                raise Exception("Geçersiz miktar: 0")

            side = "BUY" if signal == "long" else "SELL"
            positionSide = "LONG" if signal == "long" else "SHORT"
            opposite_side = "SELL" if signal == "long" else "BUY"

            log.info(f"--> Ayarlanmış Miktar: {usdt_amount} x {price:.2f} x {step_size} = {quantity}")
            self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity,
                positionSide=positionSide                
            )

            # 🎯 TP %2 - SL %2.5
            tp_price = round(price * 1.02, 4) if signal == "long" else round(price * 0.98, 4)
            sl_price = round(price * 0.975, 4) if signal == "long" else round(price * 1.025, 4)
            opposite_side = "SELL" if signal == "long" else "BUY"


            # TP emri
            self.client.futures_create_order(
                symbol=symbol,
                side=opposite_side,
                type="TAKE_PROFIT_MARKET",
                stopPrice=tp_price,
                closePosition=True,
                positionSide=positionSide,
                timeInForce="GTC"
            )

            # SL emri
            self.client.futures_create_order(
                symbol=symbol,
                side=opposite_side,
                type="STOP_MARKET",
                stopPrice=sl_price,
                closePosition=True,
                positionSide=positionSide,
                timeInForce="GTC"
            )

            return "Pozisyon açıldı, TP/SL ayarlandı."
        except Exception as e:
            log.error(f"{symbol} işlem açılamadı: {e}")
            return str(e)

    def get_step_size(self, symbol):
        try:
            info = self.client.futures_exchange_info()
            for s in info['symbols']:
                if s['symbol'] == symbol:
                    for f in s['filters']:
                        if f['filterType'] == 'LOT_SIZE':
                            step_size = float(f['stepSize'])
                            return round(-1 * (len(str(step_size).split('.')[-1].rstrip('0'))))
        except Exception as e:
            log.error(f"{symbol} step size alınamadı: {e}")
            return 0

    def has_signal(self, symbol):
        signal = self.get_signal(symbol)
        return signal is not None

    def get_rsi_value(self, symbol):
        try:
            klines = self.client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=14)
            closes = [float(kline[4]) for kline in klines]
            gains = [closes[i] - closes[i - 1] for i in range(1, len(closes)) if closes[i] > closes[i - 1]]
            losses = [closes[i - 1] - closes[i] for i in range(1, len(closes)) if closes[i] < closes[i - 1]]
            average_gain = sum(gains) / 6 if gains else 0.0001
            average_loss = sum(losses) / 6 if losses else 0.0001
            rs = average_gain / average_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception as e:
            log.error(f"{symbol} RSI değeri alınamadı: {e}")
            return 50.0

    def has_open_position(self, symbol, position_side):
        try:
            positions = self.client.futures_position_information(symbol=symbol)
            for pos in positions:
                if pos["positionSide"] == position_side.upper() and float(pos['positionAmt']) != 0:
                    return True
            return False
        except Exception as e:
            log.error(f"{symbol} pozisyon kontrol hatası: {e}")
            return False

    def adjust_tp_sl(self, symbol, position_side, entry_price):
        try:
            price = float(self.client.futures_symbol_ticker(symbol=symbol)['price'])
            opposite_side = "SELL" if position_side.upper() == "LONG" else "BUY"
            # 🎯 TP %2 - SL %2.5
            tp_price = round(entry_price * 1.02, 4) if position_side == "LONG" else round(entry_price * 0.98, 4)
            sl_price = round(entry_price * 0.975, 4) if position_side == "LONG" else round(entry_price * 1.025, 4)

            self.client.futures_cancel_all_open_orders(symbol=symbol)

            self.client.futures_create_order(
                symbol=symbol,
                side=opposite_side,
                type="TAKE_PROFIT_MARKET",
                stopPrice=tp_price,
                closePosition=True,
                positionSide=position_side.upper(),
                timeInForce="GTC"
            )

            self.client.futures_create_order(
                symbol=symbol,
                side=opposite_side,
                type="STOP_MARKET",
                stopPrice=sl_price,
                closePosition=True,
                positionSide=position_side.upper(),
                timeInForce="GTC"
            )

            log.info(f"{symbol} ➜ TP/SL başarıyla güncellendi.")
        except Exception as e:
            log.error(f"{symbol} ➜ TP/SL güncellenemedi: {e}")

