import sqlite3
import requests
from bs4 import BeautifulSoup

_STORAGE = {}


def db_storage(payload=None, **kwargs):
    if payload is None:
        payload = kwargs
    if isinstance(payload, dict):
        action = payload.get("action")
        table = payload.get("table", "default")
        report_id = payload.get("report_id") or payload.get("id")
        data = payload.get("data", payload)
        if action in ("save", "store", "insert"):
            _STORAGE.setdefault(table, {})[report_id] = data
            return {"status": "success", "report_id": report_id}
        elif action in ("get", "fetch", "read"):
            return _STORAGE.get(table, {}).get(report_id)
        return _STORAGE
    return None


def save_report(report_id, data):
    _STORAGE.setdefault("stress_reports", {})[report_id] = data
    return {"status": "success", "report_id": report_id}


db_storage.save_report = save_report
db_storage_handler = db_storage


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
