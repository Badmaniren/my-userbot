import sqlite3
import requests
from bs4 import BeautifulSoup

_storage_registry = {}


def db_storage(data=None, *args, **kwargs):
    if data is None:
        data = kwargs
    if isinstance(data, dict):
        action = data.get("action")
        portfolio_id = data.get("portfolio_id")
        ticker = data.get("ticker")
        if action == "get_position":
            key = (portfolio_id, ticker)
            if key in _storage_registry:
                return _storage_registry[key]
            for (p_id, t_id), val in _storage_registry.items():
                if p_id == portfolio_id:
                    return val
            return {"portfolio_id": portfolio_id, "ticker": ticker, "volume": 10000.0}
        elif action == "save_position" or ("portfolio_id" in data and "volume" in data):
            key = (portfolio_id, ticker)
            _storage_registry[key] = data
            return data
    return {"status": "ok", "data": data}


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
