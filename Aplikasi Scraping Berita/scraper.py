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

    def __init__(
        self,
        headless=True,
        delay=2,
        limit=20,
        start_date=None,
        end_date=None,
        progress_callback=None,
        max_workers=5
    ):

        self.headless = headless
        self.delay = delay
        self.limit = limit
        self.start_date = start_date
        self.end_date = end_date
        self.progress_callback = progress_callback
        self.max_workers = max_workers

        self.visited_links = set()

        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (X11; Linux x86_64)",
        ]

        self.driver = self.create_driver()

    # -------------------------------------------------
    # DRIVER FACTORY
    # -------------------------------------------------

    def create_driver(self):

        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_options.add_argument(
            f"user-agent={random.choice(self.user_agents)}"
        )

        service = Service(ChromeDriverManager().install())

        return webdriver.Chrome(
            service=service,
            options=chrome_options
        )

    # -------------------------------------------------
    # HUMAN SIMULATION
    # -------------------------------------------------

    def human_delay(self):
        time.sleep(random.uniform(1.5, 3.5))

    def simulate_reading(self, driver):

        scrolls = random.randint(2, 5)

        for _ in range(scrolls):

            driver.execute_script(
                "window.scrollBy(0, window.innerHeight/2);"
            )

            time.sleep(random.uniform(0.5, 1.5))

    # -------------------------------------------------
    # TEXT CLEANING
    # -------------------------------------------------

    def clean_text(self, text):

        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n+", " ", text)

        return text.strip()

    # -------------------------------------------------
    # URL UTILITIES
    # -------------------------------------------------

    def normalize_url(self, base, link):

        return urljoin(base, link)

    def same_domain(self, base, link):

        base_domain = urlparse(base).netloc
        link_domain = urlparse(link).netloc

        return base_domain in link_domain

    # -------------------------------------------------
    # ARTICLE LINK DETECTION
    # -------------------------------------------------

    def detect_article_links(self, url):

        logging.info("Scanning for article links...")

        self.driver.get(url)
        self.human_delay()

        anchors = self.driver.find_elements(By.TAG_NAME, "a")

        links = set()

        for a in anchors:

            href = a.get_attribute("href")

            if not href:
                continue

            href = self.normalize_url(url, href)

            if not self.same_domain(url, href):
                continue

            if href in self.visited_links:
                continue

            if len(href.split("/")) > 4:
                links.add(href)

        logging.info(f"Article candidates: {len(links)}")

        return list(links)

    # -------------------------------------------------
    # PAGINATION DETECTOR
    # -------------------------------------------------

    def detect_pagination(self):

        pagination_links = set()

        anchors = self.driver.find_elements(By.TAG_NAME, "a")

        keywords = ["page", "halaman", "?page="]

        for a in anchors:

            href = a.get_attribute("href")

            if not href:
                continue

            if any(k in href.lower() for k in keywords):
                pagination_links.add(href)

        return list(pagination_links)

    # -------------------------------------------------
    # PARAGRAPH FILTER
    # -------------------------------------------------

    def is_valid_paragraph(self, text):

        text = text.strip()

        if len(text) < 40:
            return False

        blacklist = [
            "baca juga",
            "advertisement",
            "related",
            "follow us",
            "share this"
        ]

        lower = text.lower()

        for word in blacklist:
            if word in lower:
                return False

        return True

    # -------------------------------------------------
    # EXTRACTION METHODS
    # -------------------------------------------------

    def extract_title(self, driver):

        selectors = [
            (By.TAG_NAME, "h1"),
            (By.CSS_SELECTOR, "h1.title"),
            (By.CSS_SELECTOR, ".article-title"),
        ]

        for by, selector in selectors:

            try:
                title = driver.find_element(by, selector).text

                if title:
                    return self.clean_text(title)

            except:
                continue

        return ""

    def extract_date(self, driver):

        selectors = [
            "//time",
            "//span[contains(@class,'date')]",
            "//p[contains(@class,'date')]"
        ]

        for selector in selectors:

            try:

                element = driver.find_element(By.XPATH, selector)

                text = element.text

                if text:
                    return self.clean_text(text)

            except:
                continue

        return ""

    def extract_content(self, driver):

        paragraphs = []

        try:

            containers = driver.find_elements(
                By.CSS_SELECTOR,
                "article, .article-content, .post-content"
            )

            if containers:

                p_tags = containers[0].find_elements(By.TAG_NAME, "p")

            else:

                p_tags = driver.find_elements(By.TAG_NAME, "p")

            for p in p_tags:

                text = p.text

                if self.is_valid_paragraph(text):
                    paragraphs.append(text)

        except:
            pass

        content = " ".join(paragraphs)

        return self.clean_text(content)

    # -------------------------------------------------
    # SINGLE ARTICLE SCRAPER
    # -------------------------------------------------

    def scrape_article(self, link):

        driver = self.create_driver()

        try:

            logging.info(f"Scraping article: {link}")

            driver.get(link)

            self.human_delay()

            self.simulate_reading(driver)

            title = self.extract_title(driver)

            content = self.extract_content(driver)

            date = self.extract_date(driver)

            if not title or not content:
                return None

            return {
                "title": title,
                "date": date,
                "content": content,
                "url": link
            }

        except Exception as e:

            logging.error(f"Article error: {e}")

            return None

        finally:

            driver.quit()

    # -------------------------------------------------
    # DATE FILTER
    # -------------------------------------------------

    def filter_by_date(self, article):

        if not article["date"]:
            return True

        try:

            date_obj = datetime.strptime(
                article["date"],
                "%d %B %Y"
            )

            if self.start_date and date_obj < self.start_date:
                return False

            if self.end_date and date_obj > self.end_date:
                return False

        except:
            return True

        return True

    # -------------------------------------------------
    # PARALLEL SCRAPING
    # -------------------------------------------------

    def scrape_articles_parallel(self, links):

        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:

            futures = {
                executor.submit(self.scrape_article, link): link
                for link in links
            }

            for i, future in enumerate(as_completed(futures)):

                article = future.result()

                if article and self.filter_by_date(article):
                    results.append(article)

                if self.progress_callback:

                    progress = int(
                        (i + 1) / len(links) * 100
                    )

                    self.progress_callback(progress)

        return results

    # -------------------------------------------------
    # MAIN SCRAPER PIPELINE
    # -------------------------------------------------

    def scrape(self, url):

        links = self.detect_article_links(url)

        pagination = self.detect_pagination()

        for page in pagination:

            if len(links) >= self.limit:
                break

            try:

                self.driver.get(page)

                self.human_delay()

                new_links = self.detect_article_links(page)

                links.extend(new_links)

            except:
                continue

        links = list(set(links))[:self.limit]

        logging.info(f"Total articles to scrape: {len(links)}")

        results = self.scrape_articles_parallel(links)

        self.driver.quit()

        logging.info(f"Scraping finished. {len(results)} articles collected.")

        return results


# -------------------------------------------------
# WRAPPER FUNCTION (USED BY worker.py)
# -------------------------------------------------

def scrape_news(
    url,
    limit=20,
    start_date=None,
    end_date=None,
    progress_callback=None
):

    scraper = NewsScraper(
        headless=True,
        delay=2,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        progress_callback=progress_callback
    )

    return scraper.scrape(url)