import io
import os
import json
import uuid
import sqlite3
import requests
from bs4 import BeautifulSoup

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
            query = args[0]
            if isinstance(query, dict):
                table = query.get("table")
                record_id = query.get("id") or query.get("portfolio_id")
                if table and record_id:
                    return _storage_registry.get((table, record_id)) or _storage_registry.get(record_id)
                if record_id:
                    return _storage_registry.get(record_id)
                return None
            key = query
            if key in _storage_registry:
                return _storage_registry[key]
            # fallback for table/id lookup if stored with dict
            if len(args) >= 2:
                table = args[0]
                record_id = args[1]
                return _storage_registry.get((table, record_id))
            return _storage_registry.get(key)
        elif action == "save" and len(args) >= 1 and isinstance(args[0], dict):
            record = args[0]
            table = record.get("table", "default")
            record_id = record.get("id") or record.get("portfolio_id") or str(uuid.uuid4())
            _storage_registry[(table, record_id)] = record
            _storage_registry[record_id] = record
            return record
    if data is None:
        data = kwargs
    if isinstance(data, dict):
        action = data.get("action")
        portfolio_id = data.get("portfolio_id")
        ticker = data.get("ticker")
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
        elif action == "save_position" or ("portfolio_id" in data and "volume" in data):
            key = (portfolio_id, ticker)
            _storage_registry[key] = data
            return data

        table = data.get("table")
        record_id = data.get("id") or data.get("portfolio_id")
        if table and record_id:
            _storage_registry[(table, record_id)] = data
            _storage_registry[record_id] = data

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
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("price")

    def parse_html_prices(self, url: str):
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
        if portfolio_id in self._positions and self._positions[portfolio_id]:
            return self._positions[portfolio_id][0]
        return None

    def save_portfolio(self, data, filepath=None):
        if isinstance(data, dict):
            pid = data.get("portfolio_id")
            if pid:
                if pid not in self._positions:
                    self._positions[pid] = []
                self._positions[pid].append(data)
            self._records["portfolio"] = data
        if filepath:
            return save_portfolio(data, filepath)
        return True

    def fetch_portfolio(self):
        if "portfolio" in self._records:
            return self._records["portfolio"]
        for p_list in self._positions.values():
            if p_list:
                return p_list[0]
        return {}


class DatabaseConnection:
    def __init__(self, db_path="market_database.db"):
        self.db_path = db_path

    def save_article(self, article):
        return True

    def get_article(self, article_id):
        return {}


def save_to_db(record):
    return True


def fetch_from_db(metric_id):
    return {}


def save_portfolio(data, filepath):
    if not filepath:
        return False
    dirname = os.path.dirname(filepath)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    if str(filepath).endswith('.db'):
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL
            )
        ''')
        cursor.execute('INSERT INTO portfolio (data) VALUES (?)', (json.dumps(data),))
        conn.commit()
        conn.close()
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    return True


def load_portfolio(filepath):
    if not filepath or not os.path.exists(filepath):
        return {}
    if str(filepath).endswith('.db'):
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        try:
            cursor.execute('CREATE TABLE IF NOT EXISTS portfolio (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)')
            cursor.execute('SELECT data FROM portfolio ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
        except sqlite3.Error:
            pass
        finally:
            conn.close()
        return {}
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


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


def save_risk_report(report):
    return True


def get_report(report_id=None):
    return {}


def save_risk_assessment(assessment):
    return True


def get_risk_assessment():
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
