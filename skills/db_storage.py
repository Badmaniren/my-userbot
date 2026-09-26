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


class DatabaseStorage:
    _portfolios = {}
    _rebalance_orders = {}
    _records = {}
    _report_states = {}

    def __init__(self, db_path: str = ":memory:", *args, **kwargs):
        self.db_path = db_path

    @property
    def portfolios(self):
        return DatabaseStorage._portfolios

    @portfolios.setter
    def portfolios(self, val):
        DatabaseStorage._portfolios = val

    @property
    def rebalance_orders(self):
        return DatabaseStorage._rebalance_orders

    @rebalance_orders.setter
    def rebalance_orders(self, val):
        DatabaseStorage._rebalance_orders = val

    def get_portfolio_state(self, portfolio_id: str) -> dict:
        return DatabaseStorage._portfolios.get(portfolio_id, {})

    def save_portfolio_state(self, portfolio_id: str, state: dict) -> None:
        DatabaseStorage._portfolios[portfolio_id] = state

    def save_rebalance_orders(self, portfolio_id: str, orders: list) -> None:
        DatabaseStorage._rebalance_orders[portfolio_id] = orders

    def get_rebalance_orders(self, portfolio_id: str) -> list:
        return DatabaseStorage._rebalance_orders.get(portfolio_id, [])

    def fetch_portfolio(self, portfolio_id: str) -> dict:
        return self.get_portfolio_state(portfolio_id)

    def save_portfolio_snapshot(self, portfolio_id: str, snapshot: dict) -> None:
        self.save_portfolio_state(portfolio_id, snapshot)

    def get_anomaly_log(self) -> list:
        return []


class DatabaseConnection:
    def __init__(self, *args, **kwargs):
        self.articles = {}

    def save_article(self, article_id, data):
        self.articles[article_id] = data

    def get_article(self, article_id):
        return self.articles.get(article_id)


def save_record(key, record):
    DatabaseStorage._records[key] = record


def get_record(key):
    return DatabaseStorage._records.get(key)


def save_report_state(key, state):
    DatabaseStorage._report_states[key] = state


def get_report_state(key):
    return DatabaseStorage._report_states.get(key)


def db_storage(data=None, *args, **kwargs):
    return DatabaseStorage()


def load_db(filename):
    parser = MarketParser()
    return parser.load_data(filename)


DBStorage = DatabaseStorage
DbStorage = DatabaseStorage
MarketStorage = DatabaseStorage
MarketDatabaseStorage = DatabaseStorage
DatabaseStorageClass = DatabaseStorage
