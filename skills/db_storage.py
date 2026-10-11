import sqlite3
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    import types
    requests = types.ModuleType("requests")
    class RequestException(Exception): pass
    requests.exceptions = types.SimpleNamespace(RequestException=RequestException)
    requests.get = lambda *args, **kwargs: None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if hasattr(requests, "get"):
            try:
                response = requests.get(url, timeout=10)
                if response is not None:
                    try:
                        data = response.json()
                    except Exception:
                        return None
                    if isinstance(data, dict):
                        return data.get("price")
            except Exception:
                return None
        return None

    def parse_html_prices(self, url: str):
        if BeautifulSoup is None or not hasattr(requests, "get"):
            return None
        try:
            response = requests.get(url, timeout=10)
            if response is not None and hasattr(response, "text"):
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


def db_storage(payload=None, **kwargs):
    return {"status": "success", "payload": payload}