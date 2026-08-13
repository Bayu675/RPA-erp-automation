# erp-automation/core/logger.py
import os
import glob
import logging
import datetime
import pandas as pd
from PIL import Image

# --- CONFIG ---
LOG_DIR = "logs"
DEBUG_IMG_DIR = "debug_images"
REPORT_FILE = "audit_rejects.csv"
MAX_DEBUG_IMAGES = 50  # Hanya simpan 50 gambar terakhir

# 1. SETUP FOLDER (Init Awal)
if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
if not os.path.exists(DEBUG_IMG_DIR): os.makedirs(DEBUG_IMG_DIR)

# 2. SETUP TEXT LOGGER
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "activity.log"),
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class BotLogger:
    @staticmethod
    def info(msg):
        print(f"ℹ️  {msg}")
        logging.info(msg)

    @staticmethod
    def warn(msg):
        print(f"⚠️  {msg}")
        logging.warning(msg)

    @staticmethod
    def error(msg):
        print(f"❌ {msg}")
        logging.error(msg)

    @staticmethod
    def save_debug_image(pil_img, prefix_name):
        """
        Simpan gambar debug dengan Timestamp + Auto Cleanup
        """
        # [FIX 1] Pastikan folder ada SETIAP KALI mau nyimpen (Anti-Crash)
        if not os.path.exists(DEBUG_IMG_DIR):
            os.makedirs(DEBUG_IMG_DIR)

        # [FIX 2] Format Nama File: YYYYMMDD_HHMMSS_NamaTag.png
        # Biar user gampang bacanya dan file ngurut berdasarkan waktu
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Bersihin nama file dari karakter aneh kalo ada
        safe_name = prefix_name.replace(" ", "_").replace(":", "-")
        filename = f"{timestamp}_{safe_name}.png"
        filepath = os.path.join(DEBUG_IMG_DIR, filename)
        
        try:
            pil_img.save(filepath)
            
            # --- AUTO CLEANUP LOGIC ---
            # Ambil semua file png, urutkan dari yang terlama
            files = sorted(glob.glob(os.path.join(DEBUG_IMG_DIR, "*.png")), key=os.path.getctime)
            
            # Kalau lebih dari batas, hapus yang paling tua
            while len(files) > MAX_DEBUG_IMAGES:
                oldest = files.pop(0)
                try:
                    os.remove(oldest)
                except:
                    pass # Ignore kalo gagal hapus (misal file lagi dibuka)
                
        except Exception as e:
            # Silent fail biar gak ganggu flow utama bot
            print(f"⚠️ Gagal save debug image: {e}")

    @staticmethod
    def log_reject_to_csv(data_dict):
        """
        Catat error ke CSV (Lebih aman dari File Locking).
        Data Dict Expectation: {'so_number': '...', 'bot_total': 0, 'screen_total': 0, 'diff': 0, 'reason': '...'}
        """
        file_path = REPORT_FILE
        
        # Tambah timestamp
        data_dict['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        df_new = pd.DataFrame([data_dict])
        
        try:
            is_new_file = not os.path.exists(file_path)
            df_new.to_csv(file_path, mode='a', header=is_new_file, index=False)
                
            print(f"📝 Laporan Error tercatat di '{REPORT_FILE}'")
            logging.info(f"Report saved to CSV: {data_dict.get('so_number', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Gagal tulis CSV: {e}")
            logging.error(f"CSV Error: {e}")