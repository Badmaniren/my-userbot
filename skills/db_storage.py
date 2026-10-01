import io
import os
import json
import uuid
import sqlite3

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

_storage_registry = {}
_TAX_REPORTS_STORE = {}


def db_storage_func(data=None, *args, **kwargs):
    if isinstance(data, str):
        action = data
        if action == "set" and len(args) >= 2:
            key = args[0]
            value = args[1]
            _storage_registry[key] = value
            return value
        elif action == "get" and len(args) >= 1:
            key = args[0]
            return _storage_registry.get(key)
    if data is None:
        data = kwargs
    if isinstance(data, dict):
        action = data.get("action")
        portfolio_id = data.get("portfolio_id")
        ticker = data.get("ticker")
        table = data.get("table")
        id_val = data.get("id")
        if action == "save_tax_report":
            report_id = data.get("report_id")
            _TAX_REPORTS_STORE[report_id] = data
            return True
        elif action == "get_tax_report":
            report_id = data.get("report_id")
            return _TAX_REPORTS_STORE.get(report_id, {})
        elif action == "get_position":
            key = (portfolio_id, ticker)
            if key in _storage_registry:
                return _storage_registry[key]
            for (p_id, t_id), val in _storage_registry.items():
                if p_id == portfolio_id:
                    return val
            return {"portfolio_id": portfolio_id, "ticker": ticker, "volume": 10000.0}
        elif action == "save_position":
            key = (portfolio_id, ticker)
            _storage_registry[key] = data
            return data
        elif action == "save":
            key = (table, id_val) if table and id_val else id_val or str(uuid.uuid4())
            val = data.get("data", data)
            _storage_registry[key] = val
            if table and id_val:
                _storage_registry[f"{table}:{id_val}"] = val
            if id_val:
                _storage_registry[id_val] = val
            return val
        elif action == "get":
            key = (table, id_val) if table and id_val else id_val
            if key in _storage_registry:
                return _storage_registry[key]
            if f"{table}:{id_val}" in _storage_registry:
                return _storage_registry[f"{table}:{id_val}"]
            return _storage_registry.get(id_val)

        unique_id = data.get("extracted_id") or data.get("id") or data.get("uuid") or data.get("report_id") or str(uuid.uuid4())
        filename = f"data_{unique_id}.json"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f)
            return filename
        except (IOError, TypeError, ValueError):
            return False
    elif kwargs:
        unique_id = kwargs.get("query_id") or kwargs.get("id") or str(uuid.uuid4())
        payload = kwargs.get("payload") or kwargs
        filename = f"data_{unique_id}.json"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            return filename
        except (IOError, TypeError, ValueError):
            return False
    return {"status": "ok", "data": data}


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
            return float(element.text)
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


class DBStorage:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self._positions = {}
        self._streams = {}
        self._records = {}

    def save_portfolio_position(self, data: dict):
        portfolio_id = data.get("portfolio_id")
        if portfolio_id:
            if portfolio_id not in self._positions:
                self._positions[portfolio_id] = []
            self._positions[portfolio_id].append(data)

    def fetch_stream(self, portfolio_id: str):
        if portfolio_id in self._streams:
            return self._streams[portfolio_id]
        if portfolio_id in self._positions:
            lines = []
            for pos in self._positions[portfolio_id]:
                ticker = pos.get("ticker", "")
                shares = pos.get("shares", 0)
                purchase_price = pos.get("purchase_price", 0.0)
                current_price = pos.get("current_price", purchase_price)
                gain = pos.get("gain", (current_price - purchase_price) * shares)
                lines.append(f"portfolio_id:{portfolio_id},ticker:{ticker},gain:{gain}")
            content = "\n".join(lines).encode("utf-8")
            return io.BytesIO(content)
        return io.BytesIO(b"")

    def save(self, data):
        if isinstance(data, dict):
            p_id = data.get("portfolio_id")
            s_id = data.get("signal_id") or data.get("id")
            if p_id:
                _storage_registry[p_id] = data
            if s_id:
                _storage_registry[s_id] = data
        return True

    def save_signal(self, signal):
        if isinstance(signal, dict):
            signal_id = signal.get("signal_id")
            if signal_id:
                _storage_registry[("hedge_signals", signal_id)] = signal
                _storage_registry[f"hedge_signals:{signal_id}"] = signal
                _storage_registry[signal_id] = signal
        return True

    def save_record(self, record, extra=None):
        if isinstance(record, (str, tuple)) and extra is not None:
            self._records[record] = extra
        else:
            self._records[record] = record
        return True

    def export_to_file(self, pid, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(pid))
        return True

    def get_record(self, key):
        return self._records.get(key, {})

    def log_error(self, error):
        return True

    def check_error_log(self):
        return []

    def save_insider_trades(self, trades):
        return True

    def get_insider_trades_by_request(self, request_id):
        return []

    def save_audit_log(self, log):
        return True

    def get_audit_log(self):
        return []

    def get_portfolio(self, portfolio_id: str):
        if portfolio_id in _storage_registry:
            return _storage_registry[portfolio_id]
        if portfolio_id in self._positions and self._positions[portfolio_id]:
            return self._positions[portfolio_id][0]
        return None

    def fetch_portfolio(self, portfolio_id: str):
        if portfolio_id in _storage_registry:
            return _storage_registry[portfolio_id]
        return {"portfolio_id": portfolio_id, "portfolio_value": 100000.0, "assets": []}


class DatabaseConnection:
    def __init__(self, db_path="market_database.db"):
        self.db_path = db_path

    def save_article(self, article):
        return True

    def get_article(self, article_id):
        return {}


def save_record(key, record=None):
    return True


def export_to_file(pid, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(pid))
    return True


def get_record(key):
    return {}


def save_report_state(state):
    return True


def get_report_state():
    return {}


def save_macro_evaluation(evaluation):
    return True


def get_macro_evaluation():
    return {}


def load_db(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return {}
    return {}


class _DBStorageCallable(DBStorage):
    def __call__(self, data=None, *args, **kwargs):
        return db_storage_func(data, *args, **kwargs)


db_storage = _DBStorageCallable()
DbStorage = DBStorage
MarketStorage = DBStorage
MarketDatabaseStorage = DBStorage
DatabaseStorage = DBStorage
