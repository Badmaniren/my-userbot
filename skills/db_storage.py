import sqlite3
import requests
from bs4 import BeautifulSoup

_var_simulations_db = {}
_in_memory_db = {}


def save_var_simulation_result(simulation_result: dict) -> bool:
    if isinstance(simulation_result, dict):
        sim_id = simulation_result.get("simulation_id") or simulation_result.get("portfolio_id")
        if sim_id:
            _var_simulations_db[sim_id] = simulation_result
            return True
    return False


def get_var_simulation_result(simulation_id: str) -> dict:
    return _var_simulations_db.get(simulation_id)


def fetch_portfolio(portfolio_id: str):
    return _in_memory_db.get(portfolio_id)


class DBStorage:
    def __init__(self, db_path: str = "default.db", **kwargs):
        self.db_path = db_path

    def save(self, key, value):
        _in_memory_db[key] = value

    def get(self, key, default=None):
        return _in_memory_db.get(key, default)


DbStorage = DBStorage
db_storage = DBStorage()


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
