import sqlite3
import requests
import json
import os
import uuid
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
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file
        self._records = {}
        self._errors = []
        self._audit_logs = []
        self._insider_trades = []
        self._anomalies = []

    def __call__(self, payload=None, identifier=None, **kwargs):
        rec_id = identifier or str(uuid.uuid4())
        self._records[rec_id] = payload or kwargs
        return rec_id

    def save(self, payload=None, identifier=None, **kwargs):
        return self.__call__(payload=payload, identifier=identifier, **kwargs)

    def save_metadata_record(self, record):
        rec_id = str(uuid.uuid4())
        self._records[rec_id] = record
        return rec_id

    def get_metadata_record(self, record_id):
        return self._records.get(record_id)

    def log_error(self, err):
        self._errors.append(err)

    def check_error_log(self):
        return list(self._errors)

    def save_record(self, record):
        return self.save_metadata_record(record)

    def get_record(self, record_id):
        return self.get_metadata_record(record_id)

    def save_insider_trades(self, trades):
        self._insider_trades.append(trades)

    def get_insider_trades_by_request(self, req_id=None):
        return list(self._insider_trades)

    def save_audit_log(self, entry):
        self._audit_logs.append(entry)

    def get_audit_log(self):
        return list(self._audit_logs)

    def save_market_state(self, state):
        rec_id = str(uuid.uuid4())
        self._records[rec_id] = state
        return rec_id

    def save_anomaly_record(self, record):
        self._anomalies.append(record)

    def get_anomaly_record(self, record_id=None):
        return list(self._anomalies)

    def save_raw_log(self, log):
        self._audit_logs.append(log)

    def insert(self, record):
        return self.save_metadata_record(record)


def load_db(filename: str):
    parser = MarketParser(filename)
    return parser.load_data(filename)


db_storage = DBStorage()
MarketStorage = MarketDatabaseStorage = DbStorage = DBStorage = DatabaseStorage = DBStorage
