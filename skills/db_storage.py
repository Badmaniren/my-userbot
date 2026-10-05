import sqlite3
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


_IN_MEMORY_STORAGE = {}


@dataclass
class MacroLiquidityRecord:
    portfolio_id: str
    scenario_id: str
    liquidity_score: float
    macro_interest_rate: float
    net_cash_flow: float
    extra_fields: Dict[str, Any] = field(default_factory=dict)


class DBStorage:
    def __init__(self, connection_string: Optional[str] = None, storage_file: str = "market_data.db", **kwargs):
        self.connection_string = connection_string or storage_file
        self.storage_file = storage_file
        self._records: Dict[str, dict] = {}
        self._mock_storage: Dict[str, dict] = {}

    def get_portfolio(self, portfolio_id: str):
        return _IN_MEMORY_STORAGE.get(portfolio_id, {"portfolio_id": portfolio_id, "assets": []})

    def save_macro_simulation(self, payload: dict):
        return True

    def save_macro_metric(self, data: dict):
        if isinstance(data, dict):
            key = data.get("id") or str(uuid.uuid4())
            _IN_MEMORY_STORAGE[key] = data
        return True

    def save_macro_liquidity_record(self, record_data: dict) -> None:
        if isinstance(record_data, dict):
            p_id = record_data.get("portfolio_id")
            if p_id:
                self._records[p_id] = record_data
                self._mock_storage[p_id] = record_data
                _IN_MEMORY_STORAGE[p_id] = record_data

    def get_macro_liquidity_record(self, portfolio_id: str) -> Optional[dict]:
        return self._records.get(portfolio_id) or self._mock_storage.get(portfolio_id) or _IN_MEMORY_STORAGE.get(portfolio_id)

    def save_record(self, data: dict):
        if isinstance(data, dict):
            key = data.get("test_id") or data.get("id") or str(uuid.uuid4())
            self._records[key] = data
            _IN_MEMORY_STORAGE[key] = data

    def store(self, key, value):
        self._records[key] = value
        _IN_MEMORY_STORAGE[key] = value

    def save(self, key, value=None):
        if value is None and isinstance(key, dict):
            k = key.get("key") or key.get("id") or str(uuid.uuid4())
            self._records[k] = key
            _IN_MEMORY_STORAGE[k] = key
        else:
            self._records[key] = value
            _IN_MEMORY_STORAGE[key] = value

    def get_record(self, key):
        return self._records.get(key) or _IN_MEMORY_STORAGE.get(key)

    def fetch_record(self, key):
        return self._records.get(key) or _IN_MEMORY_STORAGE.get(key)

    def __call__(self, payload=None):
        return db_storage(payload)


DbStorage = DBStorage


def db_storage(payload=None):
    """Функция сохранения/получения данных портфеля и симуляций в хранилище."""
    if isinstance(payload, dict):
        action = payload.get("action") or payload.get("operation")
        key = payload.get("key") or payload.get("id")
        value = payload.get("value")
        if action == "set" or action == "save":
            if key is not None:
                _IN_MEMORY_STORAGE[key] = value if value is not None else payload
            else:
                gen_key = str(uuid.uuid4())
                _IN_MEMORY_STORAGE[gen_key] = payload
            return True
        elif action == "get" and key is not None:
            return _IN_MEMORY_STORAGE.get(key)
    return True


def save_portfolio(portfolio_id: str, data: dict):
    _IN_MEMORY_STORAGE[portfolio_id] = data


def store_portfolio(portfolio_id: str, data: dict):
    _IN_MEMORY_STORAGE[portfolio_id] = data


def fetch_portfolio(portfolio_id: str) -> dict:
    if portfolio_id in _IN_MEMORY_STORAGE:
        return _IN_MEMORY_STORAGE[portfolio_id]
    return {"portfolio_id": portfolio_id}


def save_record(key: str, data):
    _IN_MEMORY_STORAGE[key] = data


def get_record(key: str):
    return _IN_MEMORY_STORAGE.get(key)


def save_macro_metric(data: dict):
    if isinstance(data, dict):
        key = data.get("id") or str(uuid.uuid4())
        _IN_MEMORY_STORAGE[key] = data
    return True


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if not requests:
            return None
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("price")

    def parse_html_prices(self, url: str):
        if not requests or not BeautifulSoup:
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
