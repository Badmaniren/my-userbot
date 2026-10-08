import sqlite3
from typing import Dict, Any, Optional

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class DBStorageCallable:
    def __init__(self):
        self._storage = {}

    def __call__(self, key=None, value=None, *args, **kwargs):
        if key is not None and value is not None:
            self._storage[key] = value
            return value
        if key is not None and value is None:
            if isinstance(key, dict):
                action = key.get("action")
                k = key.get("key") or key.get("record_id") or key.get("portfolio_id")
                v = key.get("value")
                if action in ("set", "save"):
                    if k is not None:
                        self._storage[k] = v
                    return v
                elif action in ("get", "fetch"):
                    return self._storage.get(k)
            return self._storage.get(key)
        return self._storage

    def save(self, data):
        if isinstance(data, dict):
            key = data.get("key") or data.get("id") or data.get("telemetry_id") or data.get("sentinel_event_id") or str(len(self._storage))
            self._storage[key] = data
            return True
        return False

    def save_batch(self, batch):
        if isinstance(batch, list):
            for item in batch:
                self.save(item)
            return True
        return False

    def get(self, key):
        return self._storage.get(key)


db_storage = DBStorageCallable()


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if requests is None:
            return None
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
        except Exception:
            return None
        if isinstance(data, dict):
            return data.get("price")
        return None

    def parse_html_prices(self, url: str):
        if requests is None or BeautifulSoup is None:
            return None
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            element = soup.find()
            if element and element.text:
                try:
                    return float(element.text)
                except (ValueError, TypeError):
                    return None
        except Exception:
            return None
        return None

    def fetch_and_store(self, symbol: str, price: float):
        if not isinstance(symbol, str) or not isinstance(price, (int, float)) or isinstance(price, bool):
            raise TypeError("Строгая типизация нарушена: symbol должен быть str, а price — числом.")
        
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
            (symbol, float(price))
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
