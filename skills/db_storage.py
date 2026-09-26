import sqlite3
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
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file
        self.market_states = {}
        self.anomalies = {}
        self.raw_logs = {}
        self.tables = {}

    def save_market_state(self, ticker: str, price: float, volume: float, timestamp: float = None):
        if ticker not in self.market_states:
            self.market_states[ticker] = []
        self.market_states[ticker].append({
            'ticker': ticker,
            'price': price,
            'volume': volume,
            'timestamp': timestamp
        })

    def save_anomaly_record(self, trace_id: str, record: dict):
        self.anomalies[trace_id] = record

    def get_anomaly_record(self, trace_id: str):
        return self.anomalies.get(trace_id)

    def save_raw_log(self, log_id: str, content: bytes):
        self.raw_logs[log_id] = content

    def insert(self, table: str, data: dict):
        if table not in self.tables:
            self.tables[table] = []
        self.tables[table].append(data)

    def fetch_price(self, url: str):
        return MarketParser(self.storage_file).fetch_price(url)

    def load_data(self, filename: str):
        return MarketParser(self.storage_file).load_data(filename)

    def fetch_portfolio(self):
        return {}

    def save_portfolio_snapshot(self, snapshot):
        pass

    def get_anomaly_log(self):
        return list(self.anomalies.values())


def load_db(filename: str):
    return MarketParser().load_data(filename)


DbStorage = DBStorage
MarketStorage = DBStorage
MarketDatabaseStorage = DBStorage
DatabaseStorage = DBStorage
db_storage = DBStorage()
