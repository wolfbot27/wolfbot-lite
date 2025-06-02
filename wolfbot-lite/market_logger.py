import time
from market_memory import get_major_market_snapshot

if __name__ == "__main__":
    print("[🟢] Market Logger 15 dakikalık veri kaydına başladı...")
    while True:
        try:
            get_major_market_snapshot(result=None)
            print("[📦] Veri kaydedildi.")
        except Exception as e:
            print(f"[⚠️] Veri kaydedilemedi: {e}")
        time.sleep(900)  # 15 dakika = 900 saniye
