import sqlite3
import io

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

_SHARED_CONNECTION = None
_in_memory_records = {}


def get_connection(db_path="market_data.db"):
    global _SHARED_CONNECTION
    if _SHARED_CONNECTION is None:
        _SHARED_CONNECTION = sqlite3.connect(":memory:", check_same_thread=False)
    return _SHARED_CONNECTION


def fetch_stream(portfolio_id):
    return io.BytesIO(b"")


def save_record(record_id, record):
    _in_memory_records[record_id] = record
    return True


def get_record(record_id):
    return _in_memory_records.get(record_id)


def db_storage(data=None, *args, **kwargs):
    if isinstance(data, dict):
        action = data.get("action")
        record_id = data.get("record_id") or data.get("portfolio_id")
        if action in ("save", "save_stress_test"):
            _in_memory_records[record_id] = data
            return True
        elif action == "get" and record_id:
            return _in_memory_records.get(record_id)
        _in_memory_records[str(len(_in_memory_records))] = data
        return True
    elif kwargs:
        action = kwargs.get("action")
        record_id = kwargs.get("record_id") or kwargs.get("portfolio_id")
        if action == "save" and record_id:
            _in_memory_records[record_id] = kwargs
            return True
        elif action == "get" and record_id:
            return _in_memory_records.get(record_id)
        _in_memory_records[str(len(_in_memory_records))] = kwargs
        return True
    return True


class DatabaseStorage:
    def __init__(self, db_path=":memory:", *args, **kwargs):
        self.db_path = db_path

    def fetch_stream(self, portfolio_id):
        return fetch_stream(portfolio_id)

    def save_record(self, table_or_record_id, record_id_or_data, record_data=None):
        if record_data is not None:
            key = f"{table_or_record_id}:{record_id_or_data}"
            _in_memory_records[key] = record_data
            _in_memory_records[record_id_or_data] = record_data
            return True
        _in_memory_records[table_or_record_id] = record_id_or_data
        return True

    def get_record(self, table_or_record_id, record_id=None):
        if record_id is not None:
            key = f"{table_or_record_id}:{record_id}"
            if key in _in_memory_records:
                return _in_memory_records[key]
            return _in_memory_records.get(record_id)
        return _in_memory_records.get(table_or_record_id)


DBStorage = DatabaseStorage
DbStorage = DatabaseStorage


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if requests is None:
            return None
        response = requests.get(url, timeout=10)
        try:
            data = response.json()
        except Exception:
            return None
        if isinstance(data, dict):
            return data.get("price")
        return None

    def parse_html_prices(self, url: str):
        if requests is None or BeautifulSoup is None:
            return None
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
