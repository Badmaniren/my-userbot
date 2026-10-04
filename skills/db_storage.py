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
    _shared_records: Dict[str, dict] = {}
    _shared_logs: Dict[str, dict] = {}
    _shared_audits: Dict[str, dict] = {}
    _shared_evaluations: Dict[str, dict] = {}
    _shared_macro_states: Dict[str, dict] = {}

    def __init__(self, connection_string: Optional[str] = None, storage_file: str = "market_data.db", **kwargs):
        self.connection_string = connection_string or storage_file
        self.storage_file = storage_file

    def save_macro_liquidity_record(self, record_data: dict) -> None:
        if isinstance(record_data, dict):
            p_id = record_data.get("portfolio_id") or record_data.get("run_id")
            if p_id:
                self._shared_records[p_id] = record_data

    def get_macro_liquidity_record(self, portfolio_id: str) -> Optional[dict]:
        return self._shared_records.get(portfolio_id)

    def save_record(self, data: dict, key=None):
        if isinstance(data, dict):
            k = key or data.get("run_id") or data.get("test_id") or data.get("id") or str(uuid.uuid4())
            self._shared_records[k] = data
            return k
        elif key:
            self._shared_records[key] = data
            return key

    def store(self, key, value):
        self._shared_records[key] = value

    def save(self, key, value):
        self._shared_records[key] = value

    def get_record(self, key):
        return self._shared_records.get(key)

    def fetch_record(self, key):
        return self._shared_records.get(key)

    def save_activity(self, activity):
        self._shared_records["last_activity"] = activity

    def get_last_activity(self):
        return self._shared_records.get("last_activity")

    def save_macro_liquidity(self, record):
        if isinstance(record, dict):
            k = record.get("run_id") or record.get("portfolio_id") or str(uuid.uuid4())
            self._shared_records[k] = record

    def get_macro_liquidity(self, key):
        return self._shared_records.get(key)

    def cleanup(self, test_id=None):
        if test_id and test_id in self._shared_records:
            del self._shared_records[test_id]


DbStorage = DBStorage
db_storage = DBStorage


def save_record(data, key=None):
    inst = DBStorage()
    return inst.save_record(data, key)


def get_record(key):
    inst = DBStorage()
    return inst.get_record(key)


def fetch_record(key):
    inst = DBStorage()
    return inst.fetch_record(key)


def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        if isinstance(data, (dict, list)):
            import json
            json.dump(data, f)
        else:
            f.write(str(data))


def load_data(filename):
    import os
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            if filename.endswith('.json'):
                import json
                return json.load(f)
            return f.read()
    return {}


def save_log_stream(scenario_id, data):
    DBStorage._shared_logs[scenario_id] = data


def fetch_log_stream(scenario_id):
    return DBStorage._shared_logs.get(scenario_id)


def save_audit_record(audit_key, audit_data):
    DBStorage._shared_audits[audit_key] = audit_data


def fetch_audit_record(audit_key):
    return DBStorage._shared_audits.get(audit_key)


def save_evaluation_result(record_id, data):
    DBStorage._shared_evaluations[record_id] = data


def get_evaluation_result(record_id):
    return DBStorage._shared_evaluations.get(record_id)


def save_macro_liquidity_state(run_id, state_data):
    DBStorage._shared_macro_states[run_id] = state_data


def get_macro_liquidity_state(run_id):
    return DBStorage._shared_macro_states.get(run_id)


def save_macro_metric(data):
    if isinstance(data, dict):
        k = data.get("run_id") or str(uuid.uuid4())
        DBStorage._shared_macro_states[k] = data


def db_storage_handler(payload):
    inst = DBStorage()
    if isinstance(payload, dict):
        action = payload.get("action")
        if action == "save":
            inst.save_record(payload.get("data", {}), key=payload.get("key"))
            return {"status": "success"}
        elif action == "get":
            return {"status": "success", "data": inst.get_record(payload.get("key"))}
    return {"status": "ok"}


class DatabaseConnection:
    def __init__(self, db_path="market_data.db"):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str, symbol: Optional[str] = None):
        if requests is None:
            raise RuntimeError("requests library is not available")
        response = requests.get(url, timeout=10)
        data = response.json()
        if isinstance(data, dict):
            return data.get("price")
        return data

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
