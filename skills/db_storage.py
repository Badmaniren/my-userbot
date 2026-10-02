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
        if not requests:
            return None
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("price")

    def parse_html_prices(self, url: str):
        if not requests or not BeautifulSoup:
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


_IN_MEMORY_STORAGE = {}


class DBStorage:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def get_portfolio(self, portfolio_id: str):
        return {"portfolio_id": portfolio_id, "assets": []}

    def save_macro_simulation(self, payload: dict):
        return True

    def __call__(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            return db_storage(args[0])
        elif kwargs:
            return db_storage(**kwargs)
        return db_storage()


DbStorage = DBStorage


def db_storage(*args, **kwargs):
    """Функция сохранения/получения данных портфеля и симуляций в хранилище."""
    payload = None
    if args and isinstance(args[0], dict):
        payload = args[0]
    elif kwargs:
        payload = kwargs

    if isinstance(payload, dict):
        action = payload.get("action")
        portfolio_id = payload.get("portfolio_id")
        key = payload.get("key")
        value = payload.get("value")

        if action == "save_macro_liquidity_record":
            if portfolio_id:
                _IN_MEMORY_STORAGE[f"macro_liquidity_{portfolio_id}"] = payload
            return True
        elif action == "get_macro_liquidity_record":
            if portfolio_id:
                return _IN_MEMORY_STORAGE.get(f"macro_liquidity_{portfolio_id}")
            return None
        elif action == "set" and key is not None:
            _IN_MEMORY_STORAGE[key] = value
            return True
        elif action == "get" and key is not None:
            return _IN_MEMORY_STORAGE.get(key)

    return True
