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


def db_storage_connect(db_path: str = "market_data.db"):
    return sqlite3.connect(db_path)


def db_storage_save_portfolio(conn, portfolio_data: dict) -> bool:
    if conn is None:
        return False
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolios (
            portfolio_id TEXT PRIMARY KEY,
            asset TEXT,
            value REAL,
            status TEXT,
            stress_level REAL
        )
    ''')
    cursor.execute('''
        INSERT OR REPLACE INTO portfolios (portfolio_id, asset, value, status, stress_level)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        portfolio_data.get("portfolio_id"),
        portfolio_data.get("asset"),
        portfolio_data.get("value", 0.0),
        portfolio_data.get("status", "active"),
        portfolio_data.get("stress_level", 0.0)
    ))
    conn.commit()
    return True


def db_storage_get_hedge_result(conn, portfolio_id: str) -> dict:
    if conn is None:
        return {}
    cursor = conn.cursor()
    cursor.execute(
        "SELECT portfolio_id, hedge_order_id, hedge_amount FROM hedge_results WHERE portfolio_id = ?",
        (portfolio_id,)
    )
    row = cursor.fetchone()
    if row:
        return {
            "portfolio_id": row[0],
            "hedge_order_id": row[1],
            "hedge_amount": row[2]
        }
    return {}


def fetch_portfolio(portfolio_id: str, db_path: str = "market_data.db") -> dict:
    conn = db_storage_connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT portfolio_id, asset, value, status, stress_level FROM portfolios WHERE portfolio_id = ?", (portfolio_id,))
        row = cursor.fetchone()
        if row:
            return {
                "portfolio_id": row[0],
                "asset": row[1],
                "value": row[2],
                "status": row[3],
                "stress_level": row[4]
            }
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()
    return {"portfolio_id": portfolio_id, "asset": "BTC", "value": 100000.0, "status": "active", "stress_level": 0.0}