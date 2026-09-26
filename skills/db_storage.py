import io
import sqlite3

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


_in_memory_records = {}


def fetch_stream(portfolio_id):
    return io.BytesIO(b"")


def save_record(record_id, record):
    _in_memory_records[record_id] = record
    return True


def get_record(record_id):
    return _in_memory_records.get(record_id)


def db_storage(action="get", record_id=None, record=None, **kwargs):
    if action == "save" and record_id:
        _in_memory_records[record_id] = record or kwargs
        return True
    elif action == "get" and record_id:
        return _in_memory_records.get(record_id)
    return None


class DBStorage:
    def __init__(self, db_path=":memory:"):
        self.db_path = db_path

    def fetch_stream(self, portfolio_id):
        return fetch_stream(portfolio_id)

    def save_record(self, record_id, record):
        return save_record(record_id, record)

    def get_record(self, record_id):
        return get_record(record_id)


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
