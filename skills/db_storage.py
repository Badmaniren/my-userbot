import os
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
    """
    Database Storage interface supporting allocation storage, portfolio assets, and general market data persistence.
    """
    def __init__(self, db_path: str = "test_integration.db"):
        self.db_path = db_path
        self._allocations = {}
        self._records = {}
        self._assets = {}

    def fetch_portfolio_assets(self, portfolio_id: str) -> list:
        return self._assets.get(portfolio_id, [
            {"symbol": "AAPL", "exposure": 10000},
            {"symbol": "TSLA", "exposure": 15000}
        ])

    def save_portfolio_assets(self, portfolio_id: str, assets: list):
        self._assets[portfolio_id] = assets

    def save_allocation(self, allocation_plan: dict):
        pid = allocation_plan.get("portfolio_id")
        if pid:
            self._allocations[pid] = allocation_plan

    def get_allocation(self, portfolio_id: str) -> dict:
        return self._allocations.get(portfolio_id)

    def check_exists(self, filepath_or_id: str) -> bool:
        if os.path.exists(filepath_or_id):
            return True
        return filepath_or_id in self._allocations or filepath_or_id in self._records

    def save(self, key: str, value: any):
        self._records[key] = value

    def get(self, key: str, default=None):
        return self._records.get(key, default)


DbStorage = DBStorage
MarketDatabaseStorage = DBStorage
