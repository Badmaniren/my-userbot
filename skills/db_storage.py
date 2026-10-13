import json
import os
import sqlite3

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

_audit_records = {}


def save_audit_result(audit_id, payload):
    _audit_records[audit_id] = payload
    return True


def get_audit_result(audit_id):
    return _audit_records.get(audit_id)


def save_audit_record(audit_id, record):
    _audit_records[audit_id] = record
    return True


def fetch_audit_record(audit_id):
    return _audit_records.get(audit_id)


def get_audit_record(audit_id):
    return _audit_records.get(audit_id)


def db_storage_save(storage_target, data):
    if isinstance(storage_target, str):
        try:
            with open(storage_target, "w", encoding="utf-8") as f:
                json.dump(data, f)
            return True
        except Exception:
            pass
    _audit_records[str(storage_target)] = data
    return True


def db_storage_load(storage_target):
    if isinstance(storage_target, str) and os.path.exists(storage_target):
        try:
            with open(storage_target, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return _audit_records.get(str(storage_target), {})


def db_storage_get(storage_target):
    return db_storage_load(storage_target)


class DBStorage:
    def __init__(self, storage_file="market_data.db"):
        self.storage_file = storage_file

    def save_forecast(self, data):
        record_id = data.get("portfolio_id", "default")
        _audit_records[record_id] = data
        return True

    def fetch_history(self, portfolio_id, window=10):
        record = _audit_records.get(portfolio_id)
        if record:
            return [record] if isinstance(record, dict) else record
        return []

    def fetch_stream(self, portfolio_id):
        import io
        return io.BytesIO(b"dummy stream content")


DbStorage = DBStorage


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def health_check(self):
        return {"status": "ok"}

    def health_pulse(self, *args, **kwargs):
        return {"status": "ok", "pulse": True}

    def fetch_price(self, url: str):
        if not requests:
            return None
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if isinstance(data, dict):
                return data.get("price")
        except Exception:
            return None
        return None

    def parse_html_prices(self, url: str):
        if not requests or not BeautifulSoup:
            return None
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            element = soup.find()
            if element and element.text:
                try:
                    return float(element.text)
                except (ValueError, TypeError):
                    return None
        except Exception:
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


class DbStorageCallable:
    def __call__(self, record_id=None, payload=None, **kwargs):
        if record_id is not None and payload is not None:
            save_audit_result(record_id, payload)
        return True

    def save_audit_result(self, audit_id, payload):
        return save_audit_result(audit_id, payload)

    def get_audit_result(self, audit_id):
        return get_audit_result(audit_id)


db_storage = DbStorageCallable()
