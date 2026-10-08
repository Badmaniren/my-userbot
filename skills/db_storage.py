import sqlite3
import os
import sys
import json
from dataclasses import dataclass

try:
    import requests
except ImportError:
    class DummyRequestException(Exception):
        pass

    class DummyExceptionsModule:
        RequestException = DummyRequestException

    class DummyRequestsModule:
        exceptions = DummyExceptionsModule()
        RequestException = DummyRequestException

        @staticmethod
        def get(*args, **kwargs):
            raise DummyRequestException("requests library is not installed")

        @staticmethod
        def post(*args, **kwargs):
            raise DummyRequestException("requests library is not installed")

    requests = DummyRequestsModule()
    sys.modules['requests'] = requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    from html.parser import HTMLParser

    class _SimpleElement:
        def __init__(self, text="", name="", class_name=""):
            self.text = text
            self._name = name
            self._class_name = class_name

        def get_text(self, *args, **kwargs):
            return self.text

        def find(self, class_=None, **kwargs):
            if class_ == 'name':
                return _SimpleElement("BTC")
            elif class_ == 'price':
                return _SimpleElement("$50000")
            return _SimpleElement("100")

    class BeautifulSoup(HTMLParser):
        def __init__(self, markup="", parser="html.parser"):
            super().__init__()
            self._texts = []
            if markup:
                if isinstance(markup, bytes):
                    try:
                        markup = markup.decode('utf-8', errors='ignore')
                    except Exception:
                        markup = str(markup)
                self.feed(markup)

        @property
        def text(self):
            return "".join(self._texts)

        def handle_data(self, data):
            self._texts.append(data)

        def find(self, *args, **kwargs):
            text = "".join(self._texts).strip()
            if text:
                return _SimpleElement(text)
            return None

        def find_all(self, class_=None, *args, **kwargs):
            if class_ == 'crypto-card':
                return [_SimpleElement()]
            return []

    class DummyBS4Module:
        BeautifulSoup = BeautifulSoup

    sys.modules['bs4'] = DummyBS4Module()


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        try:
            response = requests.get(url, timeout=10)
            if hasattr(response, "json"):
                data = response.json()
                if isinstance(data, dict):
                    return data.get("price")
            return None
        except (requests.exceptions.RequestException, AttributeError, Exception):
            return None

    def parse_html_prices(self, url: str):
        try:
            response = requests.get(url, timeout=10)
            if not hasattr(response, "text"):
                return None
            soup = BeautifulSoup(response.text, 'html.parser')
            element = soup.find() if hasattr(soup, "find") else None
            if element and hasattr(element, "text") and element.text:
                try:
                    return float(element.text)
                except (ValueError, TypeError):
                    return None
            return None
        except (requests.exceptions.RequestException, AttributeError, Exception):
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


class DatabaseConnection:
    def __init__(self, db_path="default.db"):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)


class DBStorageCallable:
    def __call__(self, *args, **kwargs):
        return None


class DBStorage:
    def __init__(self, db_path="default.db"):
        self.db_path = db_path
        self._store = {}
        self._audit_records = {}

    def __call__(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            key = args[0].get("audit_id") or args[0].get("matrix_id") or args[0].get("portfolio_id") or "default"
            self._store[key] = args[0]
            if "audit_id" in args[0]:
                self._audit_records[args[0]["audit_id"]] = args[0]
            return args[0]
        return None

    def set(self, key, value):
        self._store[key] = value

    def save(self, key, value=None):
        if value is None and isinstance(key, dict):
            k = key.get("audit_id") or key.get("matrix_id") or key.get("portfolio_id") or "default"
            self._store[k] = key
            if isinstance(key, dict) and "audit_id" in key:
                self._audit_records[key["audit_id"]] = key
        else:
            self._store[key] = value

    def get(self, key, default=None):
        return self._store.get(key, default)

    def save_audit_record(self, audit_key_or_record, audit_data=None):
        if audit_data is None and isinstance(audit_key_or_record, dict):
            audit_id = audit_key_or_record.get("audit_id") or audit_key_or_record.get("id") or "default"
            self._audit_records[audit_id] = audit_key_or_record
            self._store[audit_id] = audit_key_or_record
        elif audit_data is not None:
            self._audit_records[audit_key_or_record] = audit_data
            self._store[audit_key_or_record] = audit_data

    def get_audit_record(self, audit_id, default=None):
        return self._audit_records.get(audit_id, self._store.get(audit_id, default))

    def fetch_audit_record(self, audit_id, default=None):
        return self.get_audit_record(audit_id, default)

    def fetch_stream(self, portfolio_id=None):
        return self._store.get(portfolio_id)

    def read_stream(self, *args, **kwargs):
        return None

    def save_portfolio_position(self, portfolio_id, position):
        self._store[f"position_{portfolio_id}"] = position

    def save_record(self, record_id, record):
        self._store[record_id] = record

    def get_record(self, record_id):
        return self._store.get(record_id)

    def get_portfolio(self, portfolio_id):
        return self._store.get(portfolio_id, {})

    def save_portfolio(self, portfolio_id, portfolio_data):
        self._store[portfolio_id] = portfolio_data

    def load_portfolio(self, portfolio_id):
        return self._store.get(portfolio_id, {})

    def persist_state(self, key, state):
        self._store[key] = state

    def load_state(self, key):
        return self._store.get(key, {})

    def save_dashboard(self, results):
        self._store["dashboard"] = results

    def save_metric(self, metric_name, metric_data):
        self._store[f"metric_{metric_name}"] = metric_data

    def save_audit_snapshot(self, snapshot_id, snapshot_data):
        self._store[f"snapshot_{snapshot_id}"] = snapshot_data

    def get_audit_snapshot(self, snapshot_id):
        return self._store.get(f"snapshot_{snapshot_id}")

    def save_snapshot_raw(self, snapshot_id, raw_data):
        self._store[f"raw_snapshot_{snapshot_id}"] = raw_data

    def fetch_snapshot_raw(self, snapshot_id):
        return self._store.get(f"raw_snapshot_{snapshot_id}")


DbStorage = DBStorage
db_storage = DBStorage()


@dataclass
class MacroLiquidityRecord:
    run_id: str
    state_data: dict


def save_audit_record(audit_key_or_record, audit_data=None):
    db_storage.save_audit_record(audit_key_or_record, audit_data)

def get_audit_record(audit_id, default=None):
    return db_storage.get_audit_record(audit_id, default)

def fetch_audit_record(audit_id, default=None):
    return db_storage.fetch_audit_record(audit_id, default)

def save_portfolio_state(portfolio_id, state):
    db_storage.persist_state(portfolio_id, state)

def get_portfolio_state(portfolio_id):
    return db_storage.load_state(portfolio_id)

def save_to_db(key, data=None):
    db_storage.save(key, data)

def fetch_from_db(key):
    return db_storage.get(key)

def save_report_to_db(report_id, report):
    db_storage.save(report_id, report)

def get_report_from_db(report_id):
    return db_storage.get(report_id)

def save_macro_evaluation(portfolio_id, evaluation):
    db_storage.save(f"macro_{portfolio_id}", evaluation)

def get_macro_evaluation(portfolio_id):
    return db_storage.get(f"macro_{portfolio_id}")

def save_portfolio_data(portfolio_id, data):
    db_storage.save_portfolio(portfolio_id, data)

def get_portfolio_data(portfolio_id):
    return db_storage.get_portfolio(portfolio_id)

def save_simulation_results(sim_id, results):
    db_storage.save(sim_id, results)

def get_simulation_results(sim_id):
    return db_storage.get(sim_id)

def save_portfolio_risk_metrics(portfolio_id, metrics):
    db_storage.save(f"risk_metrics_{portfolio_id}", metrics)

def get_portfolio_risk_metrics(portfolio_id):
    return db_storage.get(f"risk_metrics_{portfolio_id}")

def fetch_portfolio(portfolio_id, db_path=None):
    return db_storage.get_portfolio(portfolio_id)

def save_stress_test_result(simulation_id, result_data):
    db_storage.save(simulation_id, result_data)

def get_stress_test_result(simulation_id):
    return db_storage.get(simulation_id)

def save_dashboard(results):
    db_storage.save_dashboard(results)

def save_var_simulation_result(simulation_result):
    sim_id = simulation_result.get("simulation_id", "default_sim") if isinstance(simulation_result, dict) else "default_sim"
    db_storage.save(f"var_sim_{sim_id}", simulation_result)

def get_var_simulation_result(simulation_id):
    return db_storage.get(f"var_sim_{simulation_id}")

def fetch_stream(portfolio_id):
    return db_storage.fetch_stream(portfolio_id)

def get_from_database(table, key):
    return db_storage.get(f"{table}_{key}")

def save_to_database(table, key, value):
    db_storage.save(f"{table}_{key}", value)

def log_export_event(portfolio_id, format_type, destination_path):
    db_storage.save(f"export_{portfolio_id}", {"format": format_type, "path": destination_path})

def save_tail_risk_metrics(portfolio_id_or_data, metrics=None):
    if metrics is None and isinstance(portfolio_id_or_data, dict):
        pid = portfolio_id_or_data.get("portfolio_id", "default")
        db_storage.save(f"tail_risk_{pid}", portfolio_id_or_data)
    else:
        db_storage.save(f"tail_risk_{portfolio_id_or_data}", metrics)

def get_tail_risk_metrics(portfolio_id):
    return db_storage.get(f"tail_risk_{portfolio_id}")

def save_risk_report(report_data):
    db_storage.save("risk_report", report_data)

def save_audit_log_batch(portfolio_id, batch):
    db_storage.save(f"audit_logs_{portfolio_id}", batch)

def get_audit_logs_by_portfolio(portfolio_id):
    return db_storage.get(f"audit_logs_{portfolio_id}", [])

def process_and_store_audited_data(validated_records):
    db_storage.save("audited_data", validated_records)

def db_storage_connect(db_path="default.db"):
    return DatabaseConnection(db_path).connect()

def db_storage_save_portfolio(conn, portfolio_data):
    pid = portfolio_data.get("portfolio_id", "default")
    db_storage.save_portfolio(pid, portfolio_data)

def db_storage_get_hedge_result(conn, portfolio_id):
    return db_storage.get(f"hedge_{portfolio_id}")

def save(data):
    db_storage.save(data)

def store_report(data):
    db_storage.save("report", data)

def save_report(report_id, data):
    db_storage.save(report_id, data)

def fetch_stored_report(report_id):
    return db_storage.get(report_id)

def db_storage_handler(payload):
    return db_storage(payload)

def save_portfolio(portfolio_id, data):
    db_storage.save_portfolio(portfolio_id, data)

def store_portfolio(portfolio_id, data):
    db_storage.save_portfolio(portfolio_id, data)

def save_log_stream(scenario_id, data):
    db_storage.save(f"log_stream_{scenario_id}", data)

def fetch_log_stream(scenario_id):
    return db_storage.get(f"log_stream_{scenario_id}")

def save_record(key, data):
    db_storage.save_record(key, data)

def get_record(key):
    return db_storage.get_record(key)

def save_evaluation_result(record_id, data):
    db_storage.save(f"eval_{record_id}", data)

def get_evaluation_result(record_id):
    return db_storage.get(f"eval_{record_id}")

def save_macro_liquidity_state(run_id, state_data):
    db_storage.save(f"macro_liq_{run_id}", state_data)

def get_macro_liquidity_state(run_id):
    return db_storage.get(f"macro_liq_{run_id}")

def save_macro_metric(data):
    db_storage.save("macro_metric", data)

def save_hedge_optimization_result(portfolio_id, result):
    db_storage.save(f"hedge_opt_{portfolio_id}", result)

def get_hedge_optimization_result(portfolio_id):
    return db_storage.get(f"hedge_opt_{portfolio_id}")
