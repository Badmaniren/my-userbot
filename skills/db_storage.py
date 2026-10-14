import json
import os
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

    def health_check(self):
        return True

    def health_pulse(self, *args, **kwargs):
        return True

    def fetch_price(self, url: str):
        if requests is None:
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
        if requests is None or BeautifulSoup is None:
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


class DBStorage:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def health_check(self):
        return True

    def health_pulse(self, *args, **kwargs):
        return True

    def save_data(self, filepath, data):
        save_data(filepath, data)

    def get_data(self, filepath):
        return get_data(filepath)

    def save_audit_result(self, audit_id, payload):
        save_audit_record(audit_id, payload)

    def get_audit_result(self, audit_id):
        return get_audit_record(audit_id)


db_storage = DBStorage
DbStorage = DBStorage


def save_data(filepath, data):
    if not filepath:
        return
    if isinstance(filepath, str) and filepath.endswith('.db'):
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "symbol" in item and "price" in item:
                    cursor.execute('INSERT INTO market_data (symbol, price) VALUES (?, ?)', (item["symbol"], float(item["price"])))
        conn.commit()
        conn.close()
    elif isinstance(filepath, str):
        data_to_write = data
        if isinstance(data, list):
            dict_data = {}
            for item in data:
                if isinstance(item, dict) and "symbol" in item:
                    dict_data[item["symbol"]] = {
                        "price": item.get("price"),
                        "record_id": item.get("record_id", str(uuid.uuid4()))
                    }
                else:
                    dict_data = data
                    break
            data_to_write = dict_data

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_to_write, f, ensure_ascii=False, indent=4)


def get_data(filepath):
    if not isinstance(filepath, str) or not os.path.exists(filepath):
        return []
    if filepath.endswith('.json'):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif filepath.endswith('.db'):
        parser = MarketParser(filepath)
        return parser.load_data(filepath)
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


def save_audit_result(audit_id, payload):
    save_audit_record(audit_id, payload)


def get_audit_result(audit_id):
    return fetch_audit_record(audit_id)


def db_storage_save(storage_target, data):
    save_data(storage_target, data)


def db_storage_load(storage_target):
    return get_data(storage_target)


def db_storage_get(storage_target):
    return get_data(storage_target)


_AUDIT_RECORDS = {}


def save_audit_record(audit_id, record):
    _AUDIT_RECORDS[audit_id] = record


def fetch_audit_record(audit_id):
    return _AUDIT_RECORDS.get(audit_id, {})


def get_audit_record(audit_id):
    return _AUDIT_RECORDS.get(audit_id, {})
