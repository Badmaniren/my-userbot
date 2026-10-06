import sqlite3
import requests
from bs4 import BeautifulSoup


_INTEGRITY_AUDITS = {}
_AUDIT_RECORDS = {}
_INTEGRITY_REPORTS = {}
_STORAGE = {}


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


class DbStorage:
    def __init__(self, storage_file: str = "market_data.db", **kwargs):
        self.storage_file = storage_file

    def __call__(self, query: dict = None, **kwargs):
        if isinstance(query, dict):
            action = query.get("action")
            if action == "save_integrity_audit":
                port_id = query.get("portfolio_id")
                session_id = query.get("audit_session_id")
                record = query.get("record")
                key = (port_id, session_id)
                _INTEGRITY_AUDITS[key] = record
                if session_id:
                    _INTEGRITY_AUDITS[session_id] = record
                return record
            elif action == "get_integrity_audit":
                port_id = query.get("portfolio_id")
                session_id = query.get("audit_session_id")
                key = (port_id, session_id)
                if key in _INTEGRITY_AUDITS:
                    return _INTEGRITY_AUDITS[key]
                if session_id in _INTEGRITY_AUDITS:
                    return _INTEGRITY_AUDITS[session_id]
                return None
            elif action == "save":
                key = query.get("key") or query.get("id")
                val = query.get("data") or query.get("record")
                _STORAGE[key] = val
                return val
            elif action == "get":
                key = query.get("key") or query.get("id")
                return _STORAGE.get(key)
        return None

    def get_audit_record(self, audit_id: str):
        return _AUDIT_RECORDS.get(audit_id)

    def save_audit_record(self, audit_id: str, record: dict):
        _AUDIT_RECORDS[audit_id] = record

    def save_integrity_report(self, audit_id: str, report: dict):
        _INTEGRITY_REPORTS[audit_id] = report

    def get_integrity_report(self, audit_id: str):
        return _INTEGRITY_REPORTS.get(audit_id)

    def save(self, key, data):
        _STORAGE[key] = data

    def get(self, key):
        return _STORAGE.get(key)


DBStorage = DbStorage
db_storage = DbStorage()
