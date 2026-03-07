import csv
import logging
import os
import re
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any

# Logging
def setup_logger(logger_name: str = "ScraperApp", log_file: str = "scraper.log") -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Initialize global logger
logger = setup_logger()

# Export data
def export_to_csv(data: List[Dict[str, Any]], filepath: str = None) -> bool:
    if not data:
        logger.warning("Data kosong, ekspor CSV dibatalkan.")
        return False

    # Otomatically create name if there's no filepath
    if filepath is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = f"Hasil Scraping_{timestamp}.csv"

    try:
        headers = data[0].keys()
        with open(filepath, mode='w', encoding='utf-8-sig', newline='') as file:
            file.write("sep=,\n")
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Berhasil ekspor CSV: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Gagal ekspor CSV: {e}")
        return False

def export_to_excel(data: List[Dict[str, Any]], filepath: str = None) -> bool:
    if not data:
        logger.warning("Data kosong, ekspor Excel dibatalkan.")
        return False

    if filepath is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = f"Hasil Scraping_{timestamp}.xlsx"

    try:
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        logger.info(f"Berhasil ekspor Excel: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Gagal ekspor Excel: {e}")
        return False

def clean_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    
    cleaned = re.sub(r'\s+', ' ', str(raw_text))
    return cleaned.strip()
