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


def db_storage_handler(payload):
    if not isinstance(payload, dict):
        return {"status": "error", "message": "Invalid payload format"}

    query = payload.get("query")
    if query == "save_dashboard_metric":
        portfolio_id = payload.get("portfolio_id")
        scenario_id = payload.get("scenario_id")
        report_path = payload.get("report_path")
        export_format = payload.get("export_format")

        conn = sqlite3.connect("dashboard_metrics.db")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dashboard_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id TEXT,
                scenario_id TEXT,
                report_path TEXT,
                export_format TEXT
            )
        ''')
        cursor.execute('''
            INSERT INTO dashboard_metrics (portfolio_id, scenario_id, report_path, export_format)
            VALUES (?, ?, ?, ?)
        ''', (portfolio_id, scenario_id, report_path, export_format))
        conn.commit()
        conn.close()
        return {"status": "success"}

    return {"status": "ignored"}