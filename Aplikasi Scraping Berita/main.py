import sys
import logging
from gui import NewsGUI
from utils import setup_logger

def main():
    # 1. Inisialisasi Logger (Biar ada catatan kalau error)
    logger = setup_logger(logger_name="MainApp", log_file="app_execution.log")
    logger.info("=== Aplikasi News Scraper Dimulai ===")

    try:
        # 2. Jalankan GUI Utama
        # NewsGUI() di gui.py sudah punya mainloop sendiri
        NewsGUI()
        
    except Exception as e:
        logger.error(f"Terjadi kesalahan fatal saat menjalankan aplikasi: {e}")
        sys.exit(1)
    finally:
        logger.info("=== Aplikasi News Scraper Ditutup ===")

if __name__ == "__main__":
    main()