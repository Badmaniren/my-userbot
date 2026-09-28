import json
import os
import sqlite3
import requests
from bs4 import BeautifulSoup

_GLOBAL_DB_RECORDS = {}


def save_record(key_or_path, record):
    """
    Сохраняет запись либо в файл (если передана строка с именем файла),
    либо в локальный словарь.
    """
    try:
        if isinstance(key_or_path, str) and (
            key_or_path.endswith('.json')
            or 'test_db_' in key_or_path
            or '/' in key_or_path
            or '\\' in key_or_path
        ):
            with open(key_or_path, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False)
            return True
        else:
            _GLOBAL_DB_RECORDS[str(key_or_path)] = record
            return True
    except Exception:
        return False


def get_record(key_or_path, record_id=None):
    """
    Получает запись либо из файла, либо из локального словаря.
    """
    try:
        if isinstance(key_or_path, str) and (
            key_or_path.endswith('.json')
            or 'test_db_' in key_or_path
            or '/' in key_or_path
            or '\\' in key_or_path
            or os.path.exists(key_or_path)
        ):
            if os.path.exists(key_or_path):
                with open(key_or_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
            return None
        else:
            return _GLOBAL_DB_RECORDS.get(str(key_or_path))
    except Exception:
        return None


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("price")

    def parse_html_prices(self, url: str):
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find()
        if element and element.text:
            return float(element.text)
        return None

    def fetch_and_store(self, symbol: str, price: float):
        conn = sqlite3.connect(self.storage_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        
        cursor.execute(
            'INSERT INTO market_data (symbol, price) VALUES (?, ?)',
            (symbol, price)
        )
        
        conn.commit()
        conn.close()

    def load_data(self, filename: str):
        if filename.endswith('.db'):
            conn = sqlite3.connect(filename)
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT symbol, price FROM market_data')
                rows = cursor.fetchall()
                data = [f"{row[0]},{row[1]}\n" for row in rows]
            finally:
                conn.close()
            return data
        else:
            with open(filename, 'rb') as f:
                lines = f.readlines()
                return [line.decode('utf-8') for line in lines]
