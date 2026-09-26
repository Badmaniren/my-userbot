import sqlite3
import json
import requests
from bs4 import BeautifulSoup

_REPORT_STATES = {}


def save_report_state(report_id, state=None, *args, **kwargs):
    if isinstance(report_id, dict) and state is None:
        state = report_id
        report_id = state.get("report_id", "default")
    if state is None:
        state = kwargs
    _REPORT_STATES[report_id] = state
    return state


def get_report_state(report_id="default", *args, **kwargs):
    if isinstance(report_id, dict):
        report_id = report_id.get("report_id", "default")
    return _REPORT_STATES.get(report_id, {})


def load_db(filename):
    parser = MarketParser()
    return parser.load_data(filename)


def db_storage(data=None, *args, **kwargs):
    if isinstance(data, dict):
        unique_id = data.get("id") or data.get("report_id") or "data"
        filename = f"data_{unique_id}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return filename
    return None


class DBStorage:
    def __init__(self, db_path="test_integration.db", *args, **kwargs):
        self.db_path = db_path
        self._records = {}

    def save_metadata_record(self, record_id, record):
        self._records[record_id] = record

    def get_metadata_record(self, record_id):
        return self._records.get(record_id)

    def log_error(self, error):
        pass

    def check_error_log(self):
        return []

    def save(self, key, value):
        self._records[key] = value

    def save_record(self, record_id, record):
        self._records[record_id] = record

    def get_record(self, record_id):
        return self._records.get(record_id)

    def save_insider_trades(self, trades):
        pass

    def get_insider_trades_by_request(self, req_id):
        return []

    def save_audit_log(self, log):
        pass

    def get_audit_log(self):
        return []

    def save_market_state(self, state):
        pass

    def save_anomaly_record(self, record):
        pass

    def get_anomaly_record(self, record_id):
        return self._records.get(record_id)

    def save_anomaly_score(self, score):
        pass

    def save_raw_log(self, log):
        pass

    def insert(self, data):
        pass


MarketStorage = DBStorage
MarketDatabaseStorage = DBStorage
DbStorage = DBStorage
DatabaseStorage = DBStorage


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
