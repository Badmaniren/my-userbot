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


import uuid

_STORAGE = {}
_in_memory_db = {}


def db_storage(payload=None, **kwargs):
    if payload is None:
        payload = kwargs
    elif not isinstance(payload, dict):
        payload = {"data": payload}

    action = payload.get("action")
    table = payload.get("table", "default")
    id_val = payload.get("id")
    data_val = payload.get("data")

    if action == "save":
        _STORAGE[(table, id_val)] = data_val
        return data_val
    elif action == "get":
        return _STORAGE.get((table, id_val))

    return payload


def fetch_portfolio(portfolio_id, db_path=None):
    return _in_memory_db.get(portfolio_id, {"portfolio_id": portfolio_id, "initial_value": 100000.0, "volatility": 0.2, "drift": 0.0})


def save_portfolio(portfolio_id, data):
    _in_memory_db[portfolio_id] = data
    return data


def save_audit_log(data):
    log_id = uuid.uuid4().hex
    _STORAGE[("audit_logs", log_id)] = data
    return log_id


db_storage.save_audit_log = save_audit_log
db_storage.fetch_portfolio = fetch_portfolio
db_storage.save_portfolio = save_portfolio