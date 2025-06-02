import logging

# 📄 Log formatı
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 📁 Log dosyası (UTF-8 desteği ile)
log_file = "wolfbot_log.txt"
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')  # encoding düzeltildi
file_handler.setFormatter(log_formatter)

# 🖥️ Terminal (console) için handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# 🔧 Log nesnesi
log = logging.getLogger()
log.setLevel(logging.INFO)

# ⚙️ Daha önce handler eklenmişse tekrar ekleme
if not log.hasHandlers():
    log.addHandler(file_handler)
    log.addHandler(console_handler)
