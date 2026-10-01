import sqlite3

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if requests is None:
            return None
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("price")

    def parse_html_prices(self, url: str):
        if requests is None or BeautifulSoup is None:
            return None
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
    def __init__(self, storage_file: str = "market_data.db", **kwargs):
        self.storage_file = storage_file
        self._in_memory_db = {}

    def __call__(self, action: str = None, key: str = None, value=None, **kwargs):
        if action == "set" or (key is not None and value is not None and action is None):
            self._in_memory_db[key] = value
            return value
        elif action == "get":
            return self._in_memory_db.get(key)
        elif action == "delete":
            return self._in_memory_db.pop(key, None)
        return self._in_memory_db

    def save(self, key: str, value):
        self._in_memory_db[key] = value

    def get(self, key: str, default=None):
        return self._in_memory_db.get(key, default)

    def fetch_portfolio(self, portfolio_id: str):
        return self.get(portfolio_id)


DbStorage = DBStorage
db_storage = DBStorage()


def fetch_portfolio(portfolio_id: str):
    return db_storage.fetch_portfolio(portfolio_id)
