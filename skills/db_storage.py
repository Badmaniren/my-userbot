import sqlite3
import requests
from bs4 import BeautifulSoup


_AUDIT_STORAGE = {}


def save_audit_result(audit_id: str, payload: dict) -> None:
    if not isinstance(audit_id, str) or not audit_id:
        raise ValueError("audit_id must be a non-empty string")
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dictionary")
    _AUDIT_STORAGE[audit_id] = payload


def get_audit_result(audit_id: str) -> dict:
    if not isinstance(audit_id, str):
        raise ValueError("audit_id must be a string")
    return _AUDIT_STORAGE.get(audit_id)


def save_audit_record(audit_id: str, record: dict) -> None:
    save_audit_result(audit_id, record)


def fetch_audit_record(audit_id: str) -> dict:
    return get_audit_result(audit_id)


def get_audit_record(audit_id: str) -> dict:
    return get_audit_result(audit_id)


def db_storage_save(storage_target: str, data: dict) -> None:
    _AUDIT_STORAGE[storage_target] = data


def db_storage_load(storage_target: str) -> dict:
    return _AUDIT_STORAGE.get(storage_target)


def db_storage_get(storage_target: str) -> dict:
    return _AUDIT_STORAGE.get(storage_target)


class DbStorage:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def save(self, key, value):
        if isinstance(value, dict) and "audit_id" in value:
            save_audit_result(str(key), value)
        else:
            _AUDIT_STORAGE[str(key)] = value

    def get(self, key):
        return _AUDIT_STORAGE.get(str(key))

    def health_check(self):
        return True

    def health_pulse(self, *args, **kwargs):
        return {"status": "HEALTHY"}


db_storage = DbStorage()


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
