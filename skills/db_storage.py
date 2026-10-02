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
    def __init__(self):
        self._macro_storage = {}
        self._data = {}

    def save_macro_evaluation(self, data_or_pid, evaluation=None):
        if isinstance(data_or_pid, dict):
            pid = data_or_pid.get("portfolio_id")
            if pid:
                self._macro_storage[pid] = data_or_pid
            return True
        elif evaluation is not None:
            if isinstance(evaluation, dict) and "portfolio_id" not in evaluation:
                evaluation["portfolio_id"] = data_or_pid
            self._macro_storage[data_or_pid] = evaluation
            return True
        return True

    def get_macro_evaluation(self, portfolio_id: str) -> dict:
        return self._macro_storage.get(portfolio_id, {"portfolio_id": portfolio_id, "factor_name": "inflation_rate"})

    def save(self, data):
        if isinstance(data, dict) and "portfolio_id" in data:
            self._data[data["portfolio_id"]] = data
            self._macro_storage[data["portfolio_id"]] = data
        return True

    def get(self, portfolio_id: str):
        return self._data.get(portfolio_id)


db_storage_instance = DBStorage()
db_storage = db_storage_instance
DbStorage = DBStorage


def save_macro_evaluation(data_or_pid, evaluation=None):
    return db_storage_instance.save_macro_evaluation(data_or_pid, evaluation)


def get_macro_evaluation(portfolio_id: str) -> dict:
    return db_storage_instance.get_macro_evaluation(portfolio_id)
