import sqlite3
import json

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class DbStorage:
    def __init__(self, db_path="market_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_valuations (
                    portfolio_id TEXT,
                    total_value REAL,
                    asset_allocations TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS market_anomalies (
                    asset_ticker TEXT,
                    anomaly_score REAL,
                    anomaly_type TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS insider_transactions (
                    asset_ticker TEXT,
                    transaction_type TEXT,
                    volume REAL,
                    insider_role TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS hedging_calculations (
                    portfolio_id TEXT,
                    anomalous_asset TEXT,
                    beta_sensitivity REAL,
                    required_hedge_volume REAL,
                    risk_factor REAL
                )
            """)

    def get(self, key):
        return None

    def close(self):
        if self.conn:
            self.conn.close()

    def save_portfolio_valuation(self, portfolio_id, total_value, asset_allocations):
        with self.conn:
            self.conn.execute(
                "INSERT INTO portfolio_valuations (portfolio_id, total_value, asset_allocations) VALUES (?, ?, ?)",
                (portfolio_id, total_value, json.dumps(asset_allocations))
            )

    def get_portfolio_valuation(self, portfolio_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM portfolio_valuations WHERE portfolio_id = ?", (portfolio_id,))
        row = cursor.fetchone()
        if row:
            return {
                "portfolio_id": row["portfolio_id"],
                "total_value": row["total_value"],
                "asset_allocations": json.loads(row["asset_allocations"])
            }
        return None

    def save_hedging_calculation(self, portfolio_id, anomalous_asset, beta_sensitivity, required_hedge_volume, risk_factor):
        with self.conn:
            self.conn.execute(
                "INSERT INTO hedging_calculations (portfolio_id, anomalous_asset, beta_sensitivity, required_hedge_volume, risk_factor) VALUES (?, ?, ?, ?, ?)",
                (portfolio_id, anomalous_asset, beta_sensitivity, required_hedge_volume, risk_factor)
            )

    def get_hedging_calculation(self, portfolio_id, anomalous_asset):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM hedging_calculations WHERE portfolio_id = ? AND anomalous_asset = ?",
            (portfolio_id, anomalous_asset)
        )
        row = cursor.fetchone()
        if row:
            return {
                "portfolio_id": row["portfolio_id"],
                "anomalous_asset": row["anomalous_asset"],
                "beta_sensitivity": row["beta_sensitivity"],
                "required_hedge_volume": row["required_hedge_volume"],
                "risk_factor": row["risk_factor"]
            }
        return None


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if requests is None:
            return None
        response = requests.get(url, timeout=10)
        try:
            data = response.json()
        except Exception:
            return None
        if isinstance(data, dict):
            return data.get("price")
        return None

    def parse_html_prices(self, url: str):
        if requests is None or BeautifulSoup is None:
            return None
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find()
        if element and element.text:
            try:
                return float(element.text)
            except (ValueError, TypeError):
                return None
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
