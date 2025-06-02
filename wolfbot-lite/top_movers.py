import requests
from datetime import datetime, timedelta

def get_top_movers(limit=20):
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    info = requests.get(url).json()

    now = datetime.utcnow()
    sixty_days_ago = now - timedelta(days=60)
    sixty_days_ago_ms = int(sixty_days_ago.timestamp() * 1000)

    valid_symbols = set()
    for s in info['symbols']:
        if not s['symbol'].endswith('USDT'):
            continue
        if any(x in s['symbol'] for x in ['UP', 'DOWN', 'BEAR', 'BULL']):
            continue
        if s['onboardDate'] < sixty_days_ago_ms:
            valid_symbols.add(s['symbol'])

    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    response = requests.get(url)
    data = response.json()

    movers = []
    for item in data:
        symbol = item["symbol"]
        if symbol not in valid_symbols:
            continue

        try:
            kline_url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1h&limit=2"
            kline_response = requests.get(kline_url)
            kline_data = kline_response.json()
            if len(kline_data) < 2:
                continue
            price_now = float(kline_data[-1][4])
            price_prev = float(kline_data[-2][4])
            change_percent = ((price_now - price_prev) / price_prev) * 100
        except:
            continue

        movers.append({
            "symbol": symbol,
            "priceChangePercent": change_percent
        })

    sorted_movers = sorted(movers, key=lambda x: abs(float(x["priceChangePercent"])), reverse=True)
    return [m["symbol"] for m in sorted_movers[:limit]]
