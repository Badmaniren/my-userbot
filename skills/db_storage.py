import os
import sqlite3
import json
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
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                request_id TEXT PRIMARY KEY,
                symbol TEXT,
                data TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def save(self, report_data: dict):
        if not report_data or not isinstance(report_data, dict):
            return
        request_id = report_data.get("request_id") or report_data.get("id")
        symbol = report_data.get("symbol", "")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                request_id TEXT PRIMARY KEY,
                symbol TEXT,
                data TEXT
            )
        ''')
        cursor.execute(
            'INSERT OR REPLACE INTO records (request_id, symbol, data) VALUES (?, ?, ?)',
            (request_id, symbol, json.dumps(report_data))
        )
        conn.commit()
        conn.close()

    def get_record(self, request_id: str):
        if not os.path.exists(self.db_path):
            return None
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT data FROM records WHERE request_id = ?', (request_id,))
            row = cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
            return None
        except sqlite3.OperationalError:
            return None
        finally:
            conn.close()


DatabaseStorage = DBStorage
DbStorage = DBStorage
MarketStorage = DBStorage
MarketDatabaseStorage = DBStorage
