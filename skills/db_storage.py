import sqlite3
import json
import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

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


@dataclass
class MacroLiquidityRecord:
    run_id: str
    state_data: Dict[str, Any] = field(default_factory=dict)


_STORAGE: Dict[str, Any] = {}
_REPORTS: Dict[str, Any] = {}
_PORTFOLIOS: Dict[str, Any] = {}
_SNAPSHOTS: Dict[str, Any] = {}
_AUDIT_LOGS: Dict[str, Any] = {}


class db_storage:
    def __init__(self, *args, **kwargs):
        self._in_memory_db = _PORTFOLIOS
        self._storage = _STORAGE
        self._snapshots = _SNAPSHOTS
        self._reports = _REPORTS

    def fetch_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        if snapshot_id in self._snapshots:
            return self._snapshots[snapshot_id]
        return {"id": snapshot_id, "value": 0.0}

    def save_snapshot(self, snapshot_id: str, snapshot_data: Dict[str, Any]):
        self._snapshots[snapshot_id] = snapshot_data

    def fetch_portfolio(self, portfolio_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
        return self._in_memory_db.get(portfolio_id, {"portfolio_id": portfolio_id})

    def save_portfolio(self, portfolio_id: str, data: Dict[str, Any]):
        self._in_memory_db[portfolio_id] = data

    def save(self, key: Any, data: Any = None):
        if data is None and isinstance(key, dict):
            k = key.get("id") or key.get("key") or str(len(self._storage))
            self._storage[k] = key
        else:
            self._storage[str(key)] = data

    def get(self, key: str, default: Any = None) -> Any:
        return self._storage.get(key, default)

    def get_audit_record(self, audit_id: str) -> Dict[str, Any]:
        return _AUDIT_LOGS.get(audit_id, {"audit_id": audit_id})

    def save_integrity_report(self, audit_id: str, report: Dict[str, Any]):
        _AUDIT_LOGS[audit_id] = report

    def load_data(self, filename: str):
        return MarketParser().load_data(filename)

    def __call__(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            payload = args[0]
            action = payload.get("action")
            if action == "save_integrity_audit":
                audit_id = payload.get("audit_id", "default")
                _AUDIT_LOGS[audit_id] = payload
                return {"status": "SUCCESS", "audit_id": audit_id}
            elif action == "get_integrity_audit":
                audit_id = payload.get("audit_id", "default")
                return _AUDIT_LOGS.get(audit_id, {})
            return payload
        return self


DBStorage = db_storage
DbStorage = db_storage


class DatabaseConnection:
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def close(self):
        self.conn.close()


def process_and_store_audited_data(validated_records):
    for rec in validated_records:
        k = rec.get("id", str(len(_STORAGE))) if isinstance(rec, dict) else str(len(_STORAGE))
        _STORAGE[k] = rec
    return True


def db_storage_connect(db_path: str = "market_data.db"):
    return sqlite3.connect(db_path)


def db_storage_save_portfolio(conn, portfolio_data: dict):
    pid = portfolio_data.get("portfolio_id", "default")
    _PORTFOLIOS[pid] = portfolio_data
    return True


def db_storage_get_hedge_result(conn, portfolio_id: str):
    return _STORAGE.get(f"hedge_{portfolio_id}", {})


def fetch_portfolio(portfolio_id: str, db_path: Optional[str] = None):
    return _PORTFOLIOS.get(portfolio_id, {"portfolio_id": portfolio_id})


def save_portfolio(portfolio_id: str, data: dict):
    _PORTFOLIOS[portfolio_id] = data


def store_portfolio(portfolio_id: str, data: dict):
    _PORTFOLIOS[portfolio_id] = data


def save(data: Any, val: Any = None):
    if val is not None:
        _STORAGE[str(data)] = val
    elif isinstance(data, dict):
        k = data.get("id") or data.get("key") or str(len(_STORAGE))
        _STORAGE[k] = data


def store_report(data: Any):
    if isinstance(data, dict):
        rid = data.get("report_id") or str(len(_REPORTS))
        _REPORTS[rid] = data


def save_report(report_id: str, data: Any):
    _REPORTS[report_id] = data


def fetch_stored_report(report_id: str):
    return _REPORTS.get(report_id, {})


def db_storage_handler(payload: dict):
    return {"status": "PROCESSED", "payload": payload}


def save_log_stream(scenario_id: str, data: Any):
    _STORAGE[f"log_{scenario_id}"] = data


def fetch_log_stream(scenario_id: str):
    return _STORAGE.get(f"log_{scenario_id}", None)


def save_record(key: str, data: Any):
    _STORAGE[key] = data


def get_record(key: str):
    return _STORAGE.get(key, None)


def save_audit_record(audit_key: str, audit_data: Any):
    _AUDIT_LOGS[audit_key] = audit_data


def fetch_audit_record(audit_key: str):
    return _AUDIT_LOGS.get(audit_key, None)


def get_audit_record(audit_id: str):
    return _AUDIT_LOGS.get(audit_id, {"audit_id": audit_id})


def save_integrity_report(audit_id: str, report: Any):
    _AUDIT_LOGS[audit_id] = report


def save_evaluation_result(record_id: str, data: Any):
    _STORAGE[f"eval_{record_id}"] = data


def get_evaluation_result(record_id: str):
    return _STORAGE.get(f"eval_{record_id}", None)


def save_macro_liquidity_state(run_id: str, state_data: Any):
    _STORAGE[f"macro_{run_id}"] = state_data


def get_macro_liquidity_state(run_id: str):
    return _STORAGE.get(f"macro_{run_id}", None)


def save_macro_metric(data: Any):
    if isinstance(data, dict):
        mid = data.get("id", str(len(_STORAGE)))
        _STORAGE[f"macro_metric_{mid}"] = data


def save_hedge_optimization_result(portfolio_id: str, result: Any):
    _STORAGE[f"hedge_opt_{portfolio_id}"] = result


def get_hedge_optimization_result(portfolio_id: str):
    return _STORAGE.get(f"hedge_opt_{portfolio_id}", None)
