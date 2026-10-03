import sqlite3
import requests
from bs4 import BeautifulSoup


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


class DBStorage:
    def __init__(self):
        self._in_memory_db = {}

    def __call__(self, *args, **kwargs):
        if len(args) == 1:
            return self.get(args[0])
        elif len(args) >= 2:
            return self.save(args[0], args[1])
        return self._in_memory_db

    def save(self, key, value):
        self._in_memory_db[key] = value
        return value

    def get(self, key, default=None):
        return self._in_memory_db.get(key, default)

    def load_data(self, key):
        return self.get(key, [])

    def get_data(self, key):
        return self.get(key, [])

    def save_sentiment_record(self, record):
        key = getattr(record, "id", None) or str(len(self._in_memory_db))
        self._in_memory_db[key] = record
        return record

    def fetch_portfolio(self, portfolio_id):
        return self._in_memory_db.get(portfolio_id, {"portfolio_id": portfolio_id})

    def load_portfolio(self, portfolio_id):
        return self._in_memory_db.get(portfolio_id, {"portfolio_id": portfolio_id})

    def get_portfolio_assets(self, portfolio_id):
        portfolio = self.fetch_portfolio(portfolio_id)
        if isinstance(portfolio, dict):
            return portfolio.get("assets", [])
        return []

    def save_record(self, key, data=None):
        self._in_memory_db[key] = data
        return data

    def export_to_file(self, portfolio_id, filepath):
        if filepath:
            with open(filepath, "w") as f:
                f.write("")


db_storage = DBStorage()
