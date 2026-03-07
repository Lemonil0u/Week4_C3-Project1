import time
import re
import random
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

class NewsScraper:
    def __init__(self, headless=True, delay=2, limit=20, start_date=None, end_date=None, progress_callback=None, max_workers=5):
        self.headless = headless
        self.delay = delay
        self.limit = limit
        self.start_date = start_date
        self.end_date = end_date
        self.progress_callback = progress_callback
        self.max_workers = max_workers
        self.visited_links = set()
        self.driver = self.create_driver()

    def create_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--remote-allow-origins=*")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--ignore-certificate-errors")
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def human_delay(self):
        time.sleep(random.uniform(self.delay, self.delay + 1))

    def detect_article_links(self, url):
        links = []
        try:
            self.driver.get(url)
            self.human_delay()
            a_tags = self.driver.find_elements(By.TAG_NAME, "a")
            
            for a in a_tags:
                href = a.get_attribute("href")
                if href:
                    href = urljoin(url, href)
                    if urlparse(href).netloc == urlparse(url).netloc:
                        if href not in self.visited_links:
                            # Filter: Link dalam (CNN) atau Keyword Berita (iNews/Detik)
                            pola_berita = ['/news/', '/read/', '/berita/', '/nasional/', '/detail/']
                            if len(href.split("/")) > 4 or any(x in href for x in pola_berita):
                                if len(href.split("/")[-1]) > 8: 
                                    links.append(href)
            return list(set(links))
        except Exception as e:
            logging.error(f"Error detect links: {e}")
            return []

    def extract_title(self, driver):
        selectors = [(By.TAG_NAME, "h1"), (By.CLASS_NAME, "detail-title"), (By.CSS_SELECTOR, "h1.title")]
        for by, val in selectors:
            try:
                element = driver.find_element(by, val)
                if element.text.strip(): return element.text.strip()
            except: continue
        return "No Title"

    def extract_date(self, driver):
        selectors = ["//time", "//span[contains(@class,'date')]", "//div[contains(@class,'detail-date')]"]
        for xpath in selectors:
            try:
                element = driver.find_element(By.XPATH, xpath)
                return element.text.strip()
            except: continue
        return datetime.now().strftime("%Y-%m-%d")

    def extract_content(self, driver):
        paragraphs = []
        selectors = ["article", ".detail-text", ".article-content", ".post-content", ".entry-content"]
        for sel in selectors:
            try:
                container = driver.find_element(By.CSS_SELECTOR, sel)
                p_tags = container.find_elements(By.TAG_NAME, "p")
                for p in p_tags:
                    if p.text.strip(): paragraphs.append(p.text.strip())
                if paragraphs: break
            except: continue
        return "\n".join(paragraphs) if paragraphs else "No Content Found"

    def scrape_article(self, url):
        temp_driver = self.create_driver()
        try:
            temp_driver.get(url)
            time.sleep(2)
            res = {
                "url": url,
                "title": self.extract_title(temp_driver),
                "content": self.extract_content(temp_driver),
                "date": self.extract_date(temp_driver)
            }
            return res
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return None
        finally:
            temp_driver.quit()

    def scrape(self, url):
        # Ambil link artikel dari halaman awal
        all_links = self.detect_article_links(url)
        links_to_scrape = all_links[:self.limit]
        
        logging.info(f"Ditemukan {len(links_to_scrape)} artikel untuk diproses.")
        
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.scrape_article, l): l for l in links_to_scrape}
            for i, future in enumerate(as_completed(future_to_url)):
                res = future.result()
                if res: results.append(res)
                if self.progress_callback:
                    progress = int(((i + 1) / len(links_to_scrape)) * 100)
                    self.progress_callback(progress)
        
        self.driver.quit()
        return results

def scrape_news(url, limit=20, progress_callback=None):
    # Parameter disesuaikan dengan yang dipanggil worker.py
    scraper = NewsScraper(limit=limit, progress_callback=progress_callback)
    return scraper.scrape(url)