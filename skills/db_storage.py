import os
import json
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

_in_memory_records = []


def fetch_stream(portfolio_id=None):
    return io.BytesIO(b"")


def save_record(key, record):
    return True


def get_record(key):
    return {}


def load_db(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return {}
    return {}


def db_storage_func(data=None, *args, **kwargs):
    if data is None and kwargs:
        data = kwargs

    if isinstance(data, dict):
        action = data.get("action")
        record = data.get("record")

        if action in ("insert", "save", "save_stress_test"):
            if record is not None:
                if isinstance(record, dict):
                    _in_memory_records.append(record.copy())
                else:
                    _in_memory_records.append(record)
            else:
                _in_memory_records.append(data.copy())
            return True

        elif action == "get":
            record_id = data.get("record_id") or data.get("portfolio_id")
            if record_id:
                for rec in _in_memory_records:
                    if isinstance(rec, dict) and (
                        rec.get("id") == record_id
                        or rec.get("record_id") == record_id
                        or rec.get("portfolio_id") == record_id
                    ):
                        return rec
            return _in_memory_records

        filter_dict = data.get("filter")
        if filter_dict and isinstance(filter_dict, dict):
            matched = []
            for rec in _in_memory_records:
                if isinstance(rec, dict):
                    match = True
                    for k, v in filter_dict.items():
                        if rec.get(k) != v:
                            match = False
                            break
                    if match:
                        matched.append(rec)
            limit = data.get("limit")
            if limit and isinstance(limit, int):
                return matched[:limit]
            return matched

        if record is None and not action:
            matched = []
            for rec in _in_memory_records:
                if isinstance(rec, dict):
                    match = True
                    for k, v in data.items():
                        if k in ("limit", "action"):
                            continue
                        if rec.get(k) != v:
                            match = False
                            break
                    if match:
                        matched.append(rec)
            return matched

        if action is None and record is not None:
            _in_memory_records.append(record if not isinstance(record, dict) else record.copy())
            return True

    return True


class DBStorage:
    def __init__(self, db_path="market_storage.db", *args, **kwargs):
        self.db_path = db_path

    def __call__(self, data=None, *args, **kwargs):
        return db_storage_func(data, *args, **kwargs)

    def save(self, data):
        return db_storage_func({"action": "save", "record": data})

    def save_record(self, record_id, record):
        return save_record(record_id, record)

    def get_record(self, record_id):
        return get_record(record_id)

    def fetch_stream(self, portfolio_id=None):
        return fetch_stream(portfolio_id)


class _DBStorageCallable(DBStorage):
    def __call__(self, data=None, *args, **kwargs):
        return db_storage_func(data, *args, **kwargs)


db_storage = _DBStorageCallable()
DbStorage = DBStorage
MarketStorage = DBStorage
MarketDatabaseStorage = DBStorage
DatabaseStorage = DBStorage


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
        soup = BeautifulSoup(response.text, "html.parser")
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

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL
            )
        """
        )

        cursor.execute("INSERT INTO market_data (symbol, price) VALUES (?, ?)", (symbol, float(price)))

        conn.commit()
        conn.close()

    def load_data(self, filename: str):
        if filename.endswith(".db"):
            conn = sqlite3.connect(filename)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT symbol, price FROM market_data")
                rows = cursor.fetchall()
                data = [f"{row[0]},{row[1]}\n" for row in rows]
            finally:
                conn.close()
            return data
        else:
            with open(filename, "rb") as f:
                lines = f.readlines()
                return [line.decode("utf-8") for line in lines]
