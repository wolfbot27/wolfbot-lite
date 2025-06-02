import time
import requests

# Balina eşiği (daha esnek hale getirildi → 1.000 USDT)
WHALE_ORDER_THRESHOLD = 1000

# Binance order book API (20 seviyeye kadar)
def fetch_order_book(symbol):
    url = f"https://fapi.binance.com/fapi/v1/depth?symbol={symbol}&limit=20"
    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        return response.json()
    except:
        return None

def is_whale_activity_detected(symbol):
    """
    Büyük emir (balina) algılandığında True döner.
    """
    data = fetch_order_book(symbol)
    if data is None:
        return False

    bids = data.get('bids', [])
    asks = data.get('asks', [])

    # Alım (bid) ve satım (ask) emirlerini kontrol et
    for bid in bids:
        price, quantity = float(bid[0]), float(bid[1])
        if price * quantity >= WHALE_ORDER_THRESHOLD:
            return True

    for ask in asks:
        price, quantity = float(ask[0]), float(ask[1])
        if price * quantity >= WHALE_ORDER_THRESHOLD:
            return True

    return False
