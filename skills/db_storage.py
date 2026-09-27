import io
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

    def save_record(self, key, record):
        self._records[key] = record

    def get_record(self, key):
        return self._records.get(key)

    def get_portfolio(self, portfolio_id: str):
        if portfolio_id in self._positions and self._positions[portfolio_id]:
            return self._positions[portfolio_id][0]
        return None


db_storage = DBStorage()
DbStorage = DBStorage
MarketStorage = DBStorage
MarketDatabaseStorage = DBStorage
DatabaseStorage = DBStorage
