import logging
from binance.client import Client
from config import API_KEY, API_SECRET, BASE_AMOUNT, LEVERAGE, TAKE_PROFIT_PERCENT, STOP_LOSS_PERCENT

class RiskManager:
    def __init__(self):
        self.client = Client(API_KEY, API_SECRET)
        self.recovery = {}

    def get_adjusted_amount(self, symbol, signal):
        try:
            base = BASE_AMOUNT
            leverage = LEVERAGE
            multiplier = self.recovery.get(symbol, 1)

            adjusted = base * leverage * multiplier
            logging.info(f"Ayarlanmış Miktar: {base} x {leverage} x {multiplier} = {adjusted}")
            return adjusted
        except Exception as e:
            logging.error(f"{symbol}: Miktar hesaplama hatası: {e}")
            return None

    def update_result(self, symbol, signal):
        try:
            # En son işlem sonucu burada takip ediliyor.
            result = self.client.futures_account_balance()

            # Eğer sonuç dict değilse hata üretmesin diye kontrol
            if isinstance(result, dict) and result.get("code") == -2019:
                self.recovery[symbol] = self.recovery.get(symbol, 1) + 1
                logging.info(f"[RiskManager] {symbol} için kaldıraç artırıldı. Yeni katsayı: {self.recovery[symbol]}")
            else:
                self.recovery[symbol] = 1
                logging.info(f"[RiskManager] {symbol} için işlem başarılı. Recovery sıfırlandı.")
        except Exception as e:
            logging.error(f"{symbol}: RiskManager güncelleme hatası: {e}")
