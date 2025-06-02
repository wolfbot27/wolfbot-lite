 wolfbot-lite
 Automated Binance Futures trading bot with smart strategy filters.
 🐺 Wolf Bot Lite – Automated Binance Futures Trading Bot

 Wolf Bot is a fully automated cryptocurrency trading system built with Python, designed to trade on Binance Futures using technical indicators, smart entry filters, and TP/SL management.

---

  ⚙️ Features

- ✅ Supports RSI, MACD, Volume, OBV, Trend Analysis
- ✅ Whale Tracker Integration
- ✅ Smart TP/SL Management
- ✅ Position Monitoring and Risk Analysis
- ✅ Multi-coin Volatility Scanner
- ✅ Designed for Isolated 10x leverage trades

---

🧠 Strategy Logic

Wolf Bot uses a combination of:
- **Momentum indicators** (RSI, MACD)
- **Volume filters** and whale activity
- **Trend detectors** for entry confirmations
- **Smart stop-loss and take-profit updates**
- **Position watcher** to exit trades under risk conditions

All decisions are handled by a centralized logic engine across multiple files:
- `position_analyzer.py`
- `risk_trend_analyzer.py`
- `whale_tracker.py`
- `market_profiler.py`

---

🖥️ Installation

```bash
git clone https://github.com/wolfbot27/wolfbot-lite.git
cd wolfbot-lite
pip install -r requirements.txt
