import sqlite3
import requests
from bs4 import BeautifulSoup


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file
        self._snapshots = {}
        self._anomaly_logs = {}

    def fetch_portfolio(self, portfolio_id: str):
        return self._snapshots.get(portfolio_id)

    def save_portfolio_snapshot(self, snapshot: dict):
        portfolio_id = snapshot.get("portfolio_id")
        if portfolio_id:
            self._snapshots[portfolio_id] = snapshot
            asset_data = snapshot.get("asset_data", {})
            if isinstance(asset_data, dict):
                tx_id = asset_data.get("transaction_id")
            else:
                tx_id = None
            self._anomaly_logs[portfolio_id] = {
                "portfolio_id": portfolio_id,
                "transaction_id": tx_id,
                "snapshot": snapshot
            }

    def get_anomaly_log(self, portfolio_id: str):
        return self._anomaly_logs.get(portfolio_id)

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


db_storage = MarketParser()
DbStorage = MarketParser
DBStorage = MarketParser
MarketStorage = MarketParser
MarketDatabaseStorage = MarketParser


def load_db(filename: str):
    return db_storage.load_data(filename)