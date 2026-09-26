import sqlite3
import requests
from bs4 import BeautifulSoup

_in_memory_records = {}


def save_record(store_name: str, data: dict) -> bool:
    if store_name not in _in_memory_records:
        _in_memory_records[store_name] = {}
    record_id = data.get("id") if isinstance(data, dict) else None
    if record_id:
        _in_memory_records[store_name][record_id] = data
    return True


def get_record(store_name: str, record_id: str):
    return _in_memory_records.get(store_name, {}).get(record_id)


class DBStorage:
    def save_record(self, store_name: str, data: dict) -> bool:
        return save_record(store_name, data)

    def get_record(self, store_name: str, record_id: str):
        return get_record(store_name, record_id)


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
