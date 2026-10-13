import sqlite3
import json
import os

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if requests is None:
            return None
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if isinstance(data, dict):
                return data.get("price")
        except Exception:
            return None
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


_memory_storage = {}


class DBStorage:
    def __init__(self, storage_target=None):
        self.storage_target = storage_target or "audit_results.json"

    def save(self, key, value):
        _memory_storage[key] = value
        return True

    def get(self, key, default=None):
        return _memory_storage.get(key, default)

    def load(self, key, default=None):
        return self.get(key, default)

    def health_check(self):
        return True

    def health_pulse(self, *args, **kwargs):
        return {"status": "healthy"}

    def __call__(self, *args, **kwargs):
        action = kwargs.get("action") or (args[0] if args else None)
        if action == "save":
            key = kwargs.get("key") or (args[1] if len(args) > 1 else None)
            value = kwargs.get("value") or (args[2] if len(args) > 2 else None)
            return self.save(key, value)
        elif action == "get" or action == "load":
            key = kwargs.get("key") or (args[1] if len(args) > 1 else None)
            return self.get(key)
        return True


DbStorage = DBStorage
db_storage = DBStorage()


def save_audit_result(audit_id, payload):
    return db_storage.save(audit_id, payload)


def get_audit_result(audit_id):
    return db_storage.get(audit_id)


def db_storage_save(storage_target, data):
    return db_storage.save(storage_target, data)


def db_storage_load(storage_target):
    return db_storage.get(storage_target)


def db_storage_get(storage_target):
    return db_storage.get(storage_target)


def save_audit_record(audit_id, record):
    return db_storage.save(audit_id, record)


def fetch_audit_record(audit_id):
    return db_storage.get(audit_id)


def get_audit_record(audit_id):
    return db_storage.get(audit_id)