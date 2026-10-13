import sqlite3
import json
import os
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


_in_memory_db: Dict[str, Any] = {}
_audit_records: Dict[str, Any] = {}


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

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

    def health_check(self) -> Dict[str, Any]:
        return {"status": "ok", "subsystem": "MarketParser"}

    def health_pulse(self, *args, **kwargs) -> Dict[str, Any]:
        return {"status": "healthy", "subsystem": "MarketParser"}


class DBStorage:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def save(self, key_or_data: Any, value: Any = None) -> Any:
        if value is not None:
            _in_memory_db[str(key_or_data)] = value
            return True
        elif isinstance(key_or_data, dict):
            key = key_or_data.get("id") or key_or_data.get("audit_id") or "latest"
            _in_memory_db[str(key)] = key_or_data
            return True
        else:
            _in_memory_db[str(key_or_data)] = key_or_data
            return True

    def get(self, key: str, default: Any = None) -> Any:
        return _in_memory_db.get(str(key), default)

    def load(self, key: str) -> Any:
        return self.get(key)

    def delete(self, key: str) -> bool:
        key_str = str(key)
        if key_str in _in_memory_db:
            del _in_memory_db[key_str]
            return True
        return False

    def fetch_audit(self, audit_id: str) -> Optional[Dict[str, Any]]:
        return _audit_records.get(audit_id) or _in_memory_db.get(str(audit_id))

    def health_check(self) -> Dict[str, Any]:
        return {"status": "ok", "subsystem": "DBStorage"}

    def health_pulse(self, *args, **kwargs) -> Dict[str, Any]:
        return {"status": "healthy", "subsystem": "DBStorage"}

    def __call__(self, *args, **kwargs) -> Any:
        if args:
            action = str(args[0])
            if action.startswith("save_resilience:"):
                pid = action.split(":", 1)[1]
                _in_memory_db[f"resilience:{pid}"] = kwargs.get("data", True)
                return True
            elif action.startswith("get_resilience:"):
                pid = action.split(":", 1)[1]
                return _in_memory_db.get(f"resilience:{pid}")
        return {"status": "ok"}


DbStorage = DBStorage
db_storage = DBStorage()


def save_audit_result(audit_id: str, payload: Dict[str, Any]) -> bool:
    _audit_records[audit_id] = payload
    _in_memory_db[audit_id] = payload
    return True


def get_audit_result(audit_id: str) -> Optional[Dict[str, Any]]:
    return _audit_records.get(audit_id) or _in_memory_db.get(audit_id)


def save_audit_record(audit_id: str, record: Dict[str, Any]) -> bool:
    return save_audit_result(audit_id, record)


def fetch_audit_record(audit_id: str) -> Optional[Dict[str, Any]]:
    return get_audit_result(audit_id)


def get_audit_record(audit_id: str) -> Optional[Dict[str, Any]]:
    return get_audit_result(audit_id)


def db_storage_save(storage_target: str, data: Any) -> bool:
    _in_memory_db[storage_target] = data
    return True


def db_storage_load(storage_target: str) -> Any:
    return _in_memory_db.get(storage_target)


def db_storage_get(storage_target: str) -> Any:
    return db_storage_load(storage_target)
