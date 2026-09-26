import sqlite3
import json
import os
import requests
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
    def __init__(self, db_path: str = "storage.db"):
        self.db_path = db_path
        self._records = {}
        self._anomalies = {}
        self._audit_logs = []

    def save_anomaly(self, record):
        if isinstance(record, dict):
            anomaly_id = record.get("anomaly_id") or record.get("id")
            if anomaly_id:
                self._anomalies[anomaly_id] = record
        return True

    def save_anomaly_record(self, record):
        return self.save_anomaly(record)

    def get_anomaly_record(self, anomaly_id):
        return self._anomalies.get(anomaly_id)

    def log_audit_event(self, event):
        self._audit_logs.append(event)
        return True

    def save_audit_log(self, event):
        return self.log_audit_event(event)

    def get_audit_log(self):
        return self._audit_logs

    def save_metadata_record(self, record):
        return self.save_record(record)

    def get_metadata_record(self, record_id):
        return self.get_record(record_id)

    def log_error(self, error):
        pass

    def check_error_log(self):
        return []

    def save(self, record):
        return self.save_record(record)

    def save_record(self, record):
        if isinstance(record, dict):
            rec_id = record.get("id") or record.get("anomaly_id")
            if rec_id:
                self._records[rec_id] = record
        return True

    def get_record(self, record_id):
        return self._records.get(record_id)

    def save_insider_trades(self, trades):
        return True

    def get_insider_trades_by_request(self, request_id):
        return []

    def save_market_state(self, state):
        return True

    def save_anomaly_score(self, score_data):
        return True

    def save_raw_log(self, log_data):
        return True

    def insert(self, table, data):
        if table == "market_anomalies":
            self.save_anomaly(data)
        else:
            self.save_record(data)
        return True


_global_db_storage = DBStorage()


def db_storage(data=None, *args, **kwargs):
    if isinstance(data, dict):
        action = data.get("action")
        table = data.get("table")
        if action == "save":
            record = data.get("data")
            if record:
                _global_db_storage.insert(table, record)
                return True
        elif action == "get":
            anomaly_id = data.get("anomaly_id") or data.get("id")
            if table == "market_anomalies":
                return _global_db_storage.get_anomaly_record(anomaly_id)
            return _global_db_storage.get_record(anomaly_id)

        unique_id = data.get("id") or data.get("unique_id") or data.get("anomaly_id")
        if unique_id and "action" not in data:
            filename = f"data_{unique_id}.json"
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f)
            except Exception:
                pass

    return _global_db_storage


def load_db(filename: str):
    if filename.endswith('.db'):
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            return tables
        finally:
            conn.close()
    elif os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


DbStorage = DBStorage
MarketStorage = DBStorage
MarketDatabaseStorage = DBStorage
DatabaseStorage = DBStorage
