import sqlite3
import os
import io
import json


class _RequestsProxy:
    def get(self, *args, **kwargs):
        raise NotImplementedError("requests is not installed")


class _ElementProxy:
    def __init__(self, text=""):
        self.text = text


class _Bs4Proxy:
    def __init__(self, markup="", *args, **kwargs):
        self.markup = markup

    def find(self, *args, **kwargs):
        if "<span" in self.markup and "</span>" in self.markup:
            content = self.markup.split("<span")[1].split(">")[1].split("</span")[0]
            return _ElementProxy(content)
        return None


try:
    import requests
except ImportError:
    requests = _RequestsProxy()

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = _Bs4Proxy


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if isinstance(requests, _RequestsProxy):
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
        if isinstance(requests, _RequestsProxy):
            return None
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find() if hasattr(soup, 'find') else None
        if element and hasattr(element, 'text') and element.text:
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


class DBStorage:
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self._registry = {}
        self._raw_snapshots = {}
        self._audit_snapshots = {}

    def save_snapshot_raw(self, snapshot_id: str, stream: io.BytesIO) -> None:
        if hasattr(stream, "read"):
            pos = stream.tell() if hasattr(stream, "tell") else 0
            content = stream.read()
            if hasattr(stream, "seek"):
                stream.seek(pos)
            self._raw_snapshots[snapshot_id] = content
        elif isinstance(stream, bytes):
            self._raw_snapshots[snapshot_id] = stream
        elif isinstance(stream, str):
            self._raw_snapshots[snapshot_id] = stream.encode('utf-8')

    def fetch_snapshot_raw(self, snapshot_id: str) -> io.BytesIO:
        content = self._raw_snapshots.get(snapshot_id, b"")
        return io.BytesIO(content)

    def save_audit_snapshot(self, snapshot_id: str, data: dict) -> None:
        self._audit_snapshots[snapshot_id] = data

    def get_audit_snapshot(self, snapshot_id: str) -> dict:
        return self._audit_snapshots.get(snapshot_id, {})

    def save(self, key, value):
        self._registry[key] = value
        return True

    def get(self, key, default=None):
        return self._registry.get(key, default)


DbStorage = DBStorage
db_storage = DBStorage
