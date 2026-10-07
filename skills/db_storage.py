import sqlite3
import requests
from bs4 import BeautifulSoup


class DBStorage:
    def __init__(self):
        self._data = {}

    def save(self, key, value=None):
        if value is None:
            key, value = f"key_{len(self._data)}", key
        self._data[key] = value

    def fetch_portfolio(self, portfolio_id):
        return self._data.get(portfolio_id, {"portfolio_id": portfolio_id, "initial_value": 100000.0})

    def save_portfolio(self, portfolio_id, data):
        self._data[portfolio_id] = data

    def fetch_history(self, portfolio_id, historical_window=30):
        return [{"value": 100.0} for _ in range(historical_window)]

    def fetch_stream(self, portfolio_id):
        import io
        return io.BytesIO(f"stream_data_for_{portfolio_id}".encode("utf-8"))


db_storage = DBStorage()


def save(key, value=None):
    db_storage.save(key, value)


def fetch_portfolio(portfolio_id, db_path=None):
    return db_storage.fetch_portfolio(portfolio_id)


def save_portfolio(portfolio_id, data):
    db_storage.save_portfolio(portfolio_id, data)


def fetch_history(portfolio_id, historical_window=30):
    return db_storage.fetch_history(portfolio_id, historical_window)


def fetch_stream(portfolio_id):
    return db_storage.fetch_stream(portfolio_id)


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        response = requests.get(url, timeout=10)
        try:
            data = response.json()
        except Exception:
            return None
        if isinstance(data, dict):
            return data.get("price")
        return None

    def parse_html_prices(self, url: str):
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find()
        if element and element.text:
            try:
                return float(element.text)
            except (ValueError, TypeError):
                return None
        return None

    def fetch_and_store(self, symbol: str, price: float):
        if not isinstance(symbol, str) or not isinstance(price, (int, float)) or isinstance(price, bool):
            raise TypeError("Строгая типизация нарушена: symbol должен быть str, а price — числом.")
        
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
            (symbol, float(price))
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
