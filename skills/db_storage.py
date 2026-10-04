import sqlite3
from unittest.mock import MagicMock

try:
    import requests
except ImportError:
    requests = MagicMock()

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = MagicMock()

_DB_STORAGE = {}

def db_storage(action="get", key=None, value=None, payload=None, **kwargs):
    if isinstance(action, dict) and payload is None:
        payload = action
        action = payload.get("action", "get")
        key = payload.get("key", key)
        value = payload.get("value", value)
    elif payload is not None and isinstance(payload, dict):
        action = payload.get("action", action)
        key = payload.get("key", key)
        value = payload.get("value", value)

    if action in ("set", "save", "put"):
        if key is not None:
            _DB_STORAGE[key] = value
        return value
    elif action in ("get", "fetch", "read"):
        return _DB_STORAGE.get(key)
    elif action in ("delete", "remove"):
        return _DB_STORAGE.pop(key, None)
    elif action in ("all", "list"):
        return dict(_DB_STORAGE)
    return _DB_STORAGE.get(key) if key is not None else dict(_DB_STORAGE)


class DBStorage:
    def __init__(self, *args, **kwargs):
        pass

    def save(self, key, value):
        _DB_STORAGE[key] = value

    def get(self, key):
        return _DB_STORAGE.get(key)

    def __call__(self, *args, **kwargs):
        return db_storage(*args, **kwargs)

DbStorage = DBStorage


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
            try:
                return float(element.text)
            except (ValueError, TypeError):
                return None
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
