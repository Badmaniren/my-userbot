import sqlite3
import io
import json
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

_DATABASE_STORE: Dict[str, Dict[str, Any]] = {}

def save_to_database(table: str, key: str, value: Any) -> None:
    if table not in _DATABASE_STORE:
        _DATABASE_STORE[table] = {}
    _DATABASE_STORE[table][key] = value

def get_from_database(table: str, key: str) -> Optional[Any]:
    return _DATABASE_STORE.get(table, {}).get(key)

class db_storage:
    def __init__(self, *args, **kwargs):
        pass

    def save_record(self, table=None, key=None, value=None, data=None, **kwargs) -> None:
        tbl = table or kwargs.get("table", "default")
        k = key or kwargs.get("key")
        v = value if value is not None else (data if data is not None else kwargs.get("value", kwargs.get("data")))

        if k is None and tbl is not None and v is not None:
            k = tbl
            tbl = "default"

        if tbl and k and v is not None:
            save_to_database(str(tbl), str(k), v)

    def get_record(self, table=None, key=None, **kwargs) -> Optional[Any]:
        tbl = table or kwargs.get("table")
        k = key or kwargs.get("key")

        if tbl is not None and k is not None:
            return get_from_database(str(tbl), str(k))

        if tbl is not None and k is None:
            k = tbl
            val = get_from_database("default", str(k))
            if val is not None:
                return val
            for t, db in _DATABASE_STORE.items():
                if str(k) in db:
                    return db[str(k)]
            return None

        return None

DBStorage = db_storage
DbStorage = db_storage

def open_stream(session_id: str = None, **kwargs):
    content = json.dumps({"risk_score": 0.5}).encode("utf-8")
    return io.BytesIO(content)

def fetch_portfolio(portfolio_id: str, db_path: Optional[str] = None) -> dict:
    rec = get_from_database("portfolios", portfolio_id)
    if rec is not None:
        return rec
    return {
        "portfolio_id": portfolio_id,
        "initial_value": 100000.0,
        "volatility": 0.2,
        "drift": 0.0
    }

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
