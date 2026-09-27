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


_portfolios = {}
_records = {}


class DBStorage:
    def __init__(self, db_path=None, **kwargs):
        self.db_path = db_path

    def get_portfolio(self, portfolio_id):
        return _portfolios.get(portfolio_id)

    def save_portfolio(self, portfolio):
        if isinstance(portfolio, dict) and "portfolio_id" in portfolio:
            _portfolios[portfolio["portfolio_id"]] = portfolio
        return portfolio

    def save_record(self, key, record):
        _records[key] = record

    def get_record(self, key):
        return _records.get(key)

    def __call__(self, data=None, *args, **kwargs):
        if isinstance(data, dict):
            action = data.get("action")
            if action == "save_portfolio":
                portfolio = data.get("portfolio")
                if isinstance(portfolio, dict) and "portfolio_id" in portfolio:
                    _portfolios[portfolio["portfolio_id"]] = portfolio
                return portfolio
            elif action == "get_portfolio":
                return _portfolios.get(data.get("portfolio_id"))
        return None


db_storage = DBStorage()
DbStorage = DBStorage
MarketStorage = DBStorage
MarketDatabaseStorage = DBStorage
DatabaseStorage = DBStorage