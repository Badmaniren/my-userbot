import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

_STORAGE: Dict[str, Any] = {}


@dataclass
class MacroLiquidityRecord:
    record_id: str
    data: Any


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


def process_and_store_audited_data(validated_records: list) -> dict:
    if not isinstance(validated_records, list):
        return {"success": False, "stored_count": 0, "error": "Invalid records format"}
    _STORAGE["audited_data"] = validated_records
    return {
        "success": True,
        "stored_count": len(validated_records),
        "records": validated_records
    }


def db_storage_connect(db_path: str = ":memory:"):
    return sqlite3.connect(db_path)


def db_storage_save_portfolio(conn, portfolio_data):
    if isinstance(portfolio_data, dict):
        pid = portfolio_data.get("portfolio_id", "default")
        _STORAGE[f"portfolio_{pid}"] = portfolio_data
    return True


def db_storage_get_hedge_result(conn, portfolio_id):
    return _STORAGE.get(f"hedge_result_{portfolio_id}")


def fetch_portfolio(portfolio_id: str, db_path: Optional[str] = None):
    return _STORAGE.get(f"portfolio_{portfolio_id}", {"portfolio_id": portfolio_id})


def save_report(report_id: str, data: Any):
    _STORAGE[f"report_{report_id}"] = data
    return True


def db_storage_handler(payload: Any):
    return {"status": "ok", "payload": payload}


def save_portfolio(portfolio_id: str, data: Any):
    _STORAGE[f"portfolio_{portfolio_id}"] = data
    return True


def store_portfolio(portfolio_id: str, data: Any):
    return save_portfolio(portfolio_id, data)


def save_log_stream(scenario_id: str, data: Any):
    _STORAGE[f"log_stream_{scenario_id}"] = data
    return True


def fetch_log_stream(scenario_id: str):
    return _STORAGE.get(f"log_stream_{scenario_id}")


def save_record(key: str, data: Any):
    _STORAGE[key] = data
    return True


def get_record(key: str):
    return _STORAGE.get(key)


def save_audit_record(audit_key: str, audit_data: Any):
    _STORAGE[f"audit_{audit_key}"] = audit_data
    return True


def fetch_audit_record(audit_key: str):
    return _STORAGE.get(f"audit_{audit_key}")


def save_evaluation_result(record_id: str, data: Any):
    _STORAGE[f"evaluation_{record_id}"] = data
    return True


def get_evaluation_result(record_id: str):
    return _STORAGE.get(f"evaluation_{record_id}")


def save_macro_liquidity_state(run_id: str, state_data: Any):
    _STORAGE[f"macro_liquidity_{run_id}"] = state_data
    return True


def get_macro_liquidity_state(run_id: str):
    return _STORAGE.get(f"macro_liquidity_{run_id}")


def save_macro_metric(data: Any):
    _STORAGE["macro_metric"] = data
    return True


def save_hedge_optimization_result(portfolio_id: str, result: Any):
    _STORAGE[f"hedge_opt_{portfolio_id}"] = result
    return True


def get_hedge_optimization_result(portfolio_id: str):
    return _STORAGE.get(f"hedge_opt_{portfolio_id}")


class DatabaseConnection:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)


class DBStorageClass:
    def __call__(self, *args, **kwargs):
        if args or kwargs:
            action = kwargs.get("action")
            if action == "save_portfolio":
                return save_portfolio(kwargs.get("portfolio_id"), kwargs.get("data"))
            elif action == "fetch_portfolio":
                return fetch_portfolio(kwargs.get("portfolio_id"))
        return {"status": "ok"}

    def save(self, key: str, data: Any):
        _STORAGE[key] = data
        return True

    def load(self, key: str):
        return _STORAGE.get(key)

    def get(self, key: str, default: Any = None):
        return _STORAGE.get(key, default)

    @staticmethod
    def process_and_store_audited_data(validated_records: list) -> dict:
        return process_and_store_audited_data(validated_records)

    @staticmethod
    def fetch_portfolio(portfolio_id: str, db_path: Optional[str] = None):
        return fetch_portfolio(portfolio_id, db_path)


db_storage = DBStorageClass()
DBStorage = DBStorageClass
DbStorage = DBStorageClass
