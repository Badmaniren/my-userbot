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


_portfolio_states = {}


def save_portfolio_state(portfolio_id: str, state: dict) -> None:
    _portfolio_states[portfolio_id] = state


def get_portfolio_state(portfolio_id: str) -> dict:
    return _portfolio_states.get(portfolio_id)


def load_portfolio_state(portfolio_id: str) -> dict:
    return _portfolio_states.get(portfolio_id)


class DBStorage:
    def save_portfolio_state(self, portfolio_id: str, state: dict) -> None:
        save_portfolio_state(portfolio_id, state)

    def get_portfolio_state(self, portfolio_id: str) -> dict:
        return get_portfolio_state(portfolio_id)

    def load_portfolio_state(self, portfolio_id: str) -> dict:
        return load_portfolio_state(portfolio_id)


db_storage = DBStorage()