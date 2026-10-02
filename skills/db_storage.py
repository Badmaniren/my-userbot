import sqlite3
import uuid

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
            raise RuntimeError("requests package is not installed")
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("price")

    def parse_html_prices(self, url: str):
        if requests is None or BeautifulSoup is None:
            raise RuntimeError("requests or bs4 package is not installed")
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
    def __init__(self, db_path: str = "storage.db"):
        self.db_path = db_path
        self._storage = {}

    def save(self, key, value):
        self._storage[key] = value

    def get(self, key, default=None):
        return self._storage.get(key, default)

    def get_macro_scenario_forecast(self, macro_factor_id: str):
        return self._storage.get(macro_factor_id)

    def save_macro_scenario_forecast(self, data: dict):
        if isinstance(data, dict) and "macro_factor_id" in data:
            self._storage[data["macro_factor_id"]] = data

    def log_anomaly(self, anomaly_data):
        self._storage[f"anomaly_{uuid.uuid4().hex}"] = anomaly_data

    def save_macro_event(self, event_data):
        self._storage[f"event_{uuid.uuid4().hex}"] = event_data


db_storage = DBStorage()
DbStorage = DBStorage
