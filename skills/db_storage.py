import sqlite3
import os
import json
from unittest.mock import MagicMock

try:
    import requests
except ImportError:
    requests = MagicMock()

try:
    from bs4 import BeautifulSoup
except ImportError:
    from html.parser import HTMLParser

    class _SimpleElement:
        def __init__(self, text=""):
            self.text = text

    class BeautifulSoup(HTMLParser):
        def __init__(self, markup="", parser="html.parser"):
            super().__init__()
            self._texts = []
            if markup:
                self.feed(markup)

        def handle_data(self, data):
            self._texts.append(data)

        def find(self, *args, **kwargs):
            text = "".join(self._texts).strip()
            if text:
                return _SimpleElement(text)
            return None


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        response = requests.get(url, timeout=10)
        if hasattr(response, "json"):
            data = response.json()
            if isinstance(data, dict):
                return data.get("price")
        return None

    def parse_html_prices(self, url: str):
        response = requests.get(url, timeout=10)
        if not hasattr(response, "text"):
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find() if hasattr(soup, "find") else None
        if element and hasattr(element, "text") and element.text:
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


class DatabaseConnection:
    def __init__(self, db_path="default.db"):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)


class DBStorage:
    def __init__(self, db_path="default.db"):
        self.db_path = db_path
        self._store = {}
        self._in_memory_db = {}

    def __call__(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            action = args[0].get("action")
            key = args[0].get("matrix_id") or args[0].get("portfolio_id") or "default"
            self._store[key] = args[0]
            return args[0]
        return None

    def save(self, key, value=None):
        if value is None and isinstance(key, dict):
            k = key.get("matrix_id") or key.get("portfolio_id") or "default"
            self._store[k] = key
        else:
            self._store[key] = value

    def get(self, key, default=None):
        return self._store.get(key, default)

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


DbStorage = DBStorage
db_storage = DBStorage()


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

def fetch_portfolio(portfolio_id):
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
