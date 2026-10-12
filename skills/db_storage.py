import sqlite3
import os
import json
from typing import Any, Dict, Optional, Union

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


def db_storage_save(storage_target: str, data: Dict[str, Any]) -> None:
    if not isinstance(storage_target, str):
        raise TypeError("storage_target must be a string")
    if not isinstance(data, dict):
        raise TypeError("data must be a dictionary")
    dirname = os.path.dirname(storage_target)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(storage_target, "w", encoding="utf-8") as f:
        json.dump(data, f)


def db_storage_load(storage_target: str) -> Dict[str, Any]:
    if not isinstance(storage_target, str):
        raise TypeError("storage_target must be a string")
    if not os.path.exists(storage_target):
        return {}
    with open(storage_target, "r", encoding="utf-8") as f:
        return json.load(f)


def db_storage_get(storage_target: str) -> Dict[str, Any]:
    return db_storage_load(storage_target)


def save_audit_record(audit_id: str, record: Dict[str, Any]) -> None:
    db_storage_save(f"{audit_id}.json", record)


def fetch_audit_record(audit_id: str) -> Dict[str, Any]:
    return db_storage_load(f"{audit_id}.json")


def get_audit_record(audit_id: str) -> Dict[str, Any]:
    return fetch_audit_record(audit_id)


def fetch_portfolio(portfolio_id: Optional[str] = None) -> Dict[str, Any]:
    return {"portfolio_id": portfolio_id, "status": "active"}


class DbStorage:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def save(self, record_id_or_data: Any, data: Optional[Any] = None) -> None:
        if isinstance(record_id_or_data, str) and isinstance(data, dict):
            db_storage_save(record_id_or_data, data)
        elif isinstance(record_id_or_data, dict):
            db_storage_save("storage_default.json", record_id_or_data)

    def load(self, target: str) -> Dict[str, Any]:
        return db_storage_load(target)

    def health_check(self) -> bool:
        return True

    def health_pulse(self) -> Dict[str, Any]:
        return {"status": "ok", "healthy": True}


db_storage = DbStorage()


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if requests is None:
            return None
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
        except Exception:
            return None
        if isinstance(data, dict):
            return data.get("price")
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
