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

    def save_macro_liquidity_record(self, record_data: dict) -> None:
        if isinstance(record_data, dict):
            p_id = record_data.get("portfolio_id")
            if p_id:
                self._records[p_id] = record_data
                self._mock_storage[p_id] = record_data

    def get_macro_liquidity_record(self, portfolio_id: str) -> Optional[dict]:
        return self._records.get(portfolio_id) or self._mock_storage.get(portfolio_id)

    def save_record(self, data: dict):
        if isinstance(data, dict):
            key = data.get("test_id") or data.get("id") or str(uuid.uuid4())
            self._records[key] = data

    def store(self, key, value):
        self._records[key] = value

    def save(self, key, value):
        self._records[key] = value

    def get_record(self, key):
        return self._records.get(key)

    def fetch_record(self, key):
        return self._records.get(key)


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
