import sqlite3
import requests
import json
import os
from bs4 import BeautifulSoup


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
        if filename and filename.endswith('.db'):
            conn = sqlite3.connect(filename)
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT symbol, price FROM market_data')
                rows = cursor.fetchall()
                data = [f"{row[0]},{row[1]}\n" for row in rows]
            finally:
                conn.close()
            return data
        elif filename and filename.endswith('.json'):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                return []
        else:
            try:
                with open(filename, 'rb') as f:
                    lines = f.readlines()
                    return [line.decode('utf-8') for line in lines]
            except FileNotFoundError:
                return []


class DBStorage:
    _records = {}

    def __init__(self, *args, **kwargs):
        pass

    def save_record(self, record_id: str, data: dict) -> None:
        self._records[record_id] = data

    def get_record(self, record_id: str):
        return self._records.get(record_id)

    def set(self, record_id: str, data: dict) -> None:
        self._records[record_id] = data

    def get(self, record_id: str):
        return self._records.get(record_id)

    def query(self, *args, **kwargs):
        return list(self._records.values())

    def save(self, record_id: str, data: dict) -> None:
        self._records[record_id] = data

    def get_portfolio(self, portfolio_id: str):
        return self._records.get(portfolio_id)

    def save_portfolio(self, portfolio_id: str, data: dict):
        self._records[portfolio_id] = data

    def load_portfolio(self, portfolio_id: str):
        res = None
        if portfolio_id in self._records:
            res = self._records[portfolio_id]
        elif isinstance(portfolio_id, str) and os.path.exists(portfolio_id):
            res = load_data(portfolio_id)
        else:
            res = self._records.get(portfolio_id, {})

        if isinstance(res, dict):
            out = {}
            for k, v in res.items():
                if isinstance(v, dict):
                    out[k] = v
                elif isinstance(v, (int, float)):
                    out[k] = {"quantity": 1.0, "buy_price": float(v)}
                else:
                    out[k] = {"quantity": 1.0, "buy_price": 0.0}
            return out
        elif isinstance(res, list):
            out = {}
            for i, item in enumerate(res):
                if isinstance(item, dict):
                    sym = item.get("symbol", f"item_{i}")
                    out[sym] = item
                elif isinstance(item, str):
                    out[item] = {"quantity": 1.0, "buy_price": 0.0}
                elif isinstance(item, (int, float)):
                    out[f"asset_{i}"] = {"quantity": 1.0, "buy_price": float(item)}
            return out
        return {}

    def save_portfolio_state(self, portfolio_id: str, state: dict) -> None:
        self._records[portfolio_id] = state

    def get_portfolio_state(self, portfolio_id: str) -> dict:
        return self._records.get(portfolio_id)

    def load_portfolio_state(self, portfolio_id: str) -> dict:
        return self._records.get(portfolio_id)

    def fetch_portfolio(self, portfolio_id: str):
        return self._records.get(portfolio_id, {"portfolio_id": portfolio_id})

    def fetch_stream(self, portfolio_id: str):
        return self._records.get(portfolio_id)

    def save_dashboard(self, results):
        self._records["dashboard"] = results

    def save_metric(self, metric_id, data):
        self._records[metric_id] = data

    def initialize_database(self, *args, **kwargs):
        pass

    def save_market_entity(self, entity_id, data):
        self._records[entity_id] = data

    def get_audit_trail(self, *args, **kwargs):
        return list(self._records.values())

    def save_portfolio_position(self, portfolio_id, position):
        self._records[f"pos_{portfolio_id}"] = position

    def persist_state(self, state_id, state):
        self._records[state_id] = state

    def load_state(self, state_id):
        return self._records.get(state_id)

    def __call__(self, *args, **kwargs):
        return self


db_storage = DBStorage()
DbStorage = DBStorage
DatabaseConnection = DBStorage


def load_data(filename):
    return MarketParser().load_data(filename)


def save_evaluation_result(record_id, data):
    db_storage.save_record(record_id, data)


def get_evaluation_result(record_id):
    return db_storage.get_record(record_id)


def db_storage_handler(payload):
    if isinstance(payload, dict):
        q = payload.get("query")
        if q == "save_dashboard_metric":
            db_storage.save_metric(payload.get("metric_id"), payload.get("data"))
            return True
    return db_storage


def save_portfolio_state(portfolio_id: str, state: dict) -> None:
    db_storage.save_portfolio_state(portfolio_id, state)


def get_portfolio_state(portfolio_id: str) -> dict:
    return db_storage.get_portfolio_state(portfolio_id)


def load_portfolio_state(portfolio_id: str) -> dict:
    return db_storage.load_portfolio_state(portfolio_id)


def save_to_db(key, data):
    db_storage.save_record(key, data)


def fetch_from_db(key):
    return db_storage.get_record(key)


def save_report_to_db(report_id, report):
    db_storage.save_record(report_id, report)


def get_report_from_db(report_id):
    return db_storage.get_record(report_id)


def save_macro_evaluation(portfolio_id, evaluation):
    db_storage.save_record(portfolio_id, evaluation)


def get_macro_evaluation(portfolio_id):
    return db_storage.get_record(portfolio_id)


def save_portfolio_data(portfolio_id, data):
    db_storage.save_record(portfolio_id, data)


def get_portfolio_data(portfolio_id):
    return db_storage.get_record(portfolio_id)


def save_simulation_results(sim_id, results):
    db_storage.save_record(sim_id, results)


def get_simulation_results(sim_id):
    return db_storage.get_record(sim_id)


def save_portfolio_risk_metrics(portfolio_id, metrics):
    db_storage.save_record(portfolio_id, metrics)


def get_portfolio_risk_metrics(portfolio_id):
    return db_storage.get_record(portfolio_id)


def save_portfolio(portfolio_id, payload):
    db_storage.save_portfolio(portfolio_id, payload)


def fetch_portfolio(portfolio_id):
    return db_storage.fetch_portfolio(portfolio_id)


def save_stress_test_result(simulation_id, result_data):
    db_storage.save_record(simulation_id, result_data)


def get_stress_test_result(simulation_id):
    return db_storage.get_record(simulation_id)


def save_stress_inspection_result(portfolio_id, result):
    db_storage.save_record(portfolio_id, result)


def get_stress_inspection_result(portfolio_id):
    return db_storage.get_record(portfolio_id)


def save_dashboard(results):
    db_storage.save_dashboard(results)


def save_var_simulation_result(simulation_result):
    db_storage.save_record("var_sim", simulation_result)


def get_var_simulation_result(simulation_id):
    return db_storage.get_record(simulation_id)


def save_trend_analysis_result(data):
    db_storage.save_record("trend_analysis", data)


def get_trend_analysis_result(run_id):
    return db_storage.get_record(run_id)


def save_stream_record(record):
    db_storage.save_record("stream", record)


def get_stream_record(stream_id):
    return db_storage.get_record(stream_id)


def fetch_stream(portfolio_id):
    return db_storage.fetch_stream(portfolio_id)
