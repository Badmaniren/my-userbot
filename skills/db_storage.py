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
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file
        self._insider_trades = {}
        self._audit_logs = {}

    def save_insider_trades(self, request_id: str, trades: list):
        self._insider_trades[request_id] = trades

    def get_insider_trades_by_request(self, request_id: str):
        return self._insider_trades.get(request_id, [])

    def save_audit_log(self, operation_id: str, log_data: dict):
        self._audit_logs[operation_id] = log_data

    def get_audit_log(self, operation_id: str):
        return self._audit_logs.get(operation_id, {"operation_id": operation_id, "status": "LOGGED"})

    def save_market_state(self, state):
        pass

    def save_anomaly_record(self, record):
        pass

    def get_anomaly_record(self, record_id):
        return {}

    def save_raw_log(self, log):
        pass

    def insert(self, data):
        pass


DbStorage = DBStorage
MarketStorage = DBStorage
MarketDatabaseStorage = DBStorage