import threading
from scraper import scrape_news

class ScraperWorker(threading.Thread):
    def __init__(self, url, progress_callback, finished_callback, error_callback):
        super().__init__()
        self.url = url
        self.progress_callback = progress_callback
        self.finished_callback = finished_callback
        self.error_callback = error_callback
        self.is_stopped = False

    def run(self):
        try:
            # Panggil fungsi scrape_news dari scraper.py milik temanmu
            results = scrape_news(
                url=self.url,
                limit=20,  # Bisa disesuaikan
                progress_callback=self.progress_callback
            )
            
            # Kalau user tidak menekan tombol cancel, kirim hasilnya ke GUI
            if not self.is_stopped:
                self.finished_callback(results)
                
        except Exception as e:
            self.error_callback(str(e))

    def stop(self):
        self.is_stopped = True
        # Catatan: Karena scraper.py menggunakan ThreadPoolExecutor yang synchronous,
        # proses di background mungkin tetap berjalan sampai selesai/error.
        # Tapi dengan diset True, GUI tidak akan memproses hasil datanya.