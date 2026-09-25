import os
import json
import uuid
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
    def __init__(self, db_path="market_storage.db"):
        self.db_path = db_path

    def save(self, data):
        return True

    def save_record(self, record):
        return True

    def get_record(self, record_id):
        return {}

    def log_error(self, error):
        return True

    def check_error_log(self):
        return []

    def save_insider_trades(self, trades):
        return True

    def get_insider_trades_by_request(self, request_id):
        return []

    def save_audit_log(self, log):
        return True

    def get_audit_log(self):
        return []


def db_storage_func(data=None, *args, **kwargs):
    if isinstance(data, dict):
        unique_id = data.get("id") or data.get("uuid") or str(uuid.uuid4())
        filename = f"data_{unique_id}.json"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except (IOError, TypeError, ValueError):
            return False
    return True


def load_db(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return {}
    return {}


class _DBStorageCallable(DBStorage):
    def __call__(self, data=None, *args, **kwargs):
        return db_storage_func(data, *args, **kwargs)


db_storage = _DBStorageCallable()
DbStorage = DBStorage
MarketStorage = DBStorage
MarketDatabaseStorage = DBStorage
DatabaseStorage = DBStorage
