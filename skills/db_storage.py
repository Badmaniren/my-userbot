import sqlite3
import io
import json

try:
    import requests
except ImportError:
    import types
    requests = types.ModuleType("requests")
    requests.get = lambda *args, **kwargs: None
    requests.post = lambda *args, **kwargs: None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        response = requests.get(url, timeout=10)
        data = response.json() if hasattr(response, "json") else {}
        return data.get("price")

    def parse_html_prices(self, url: str):
        if BeautifulSoup is None:
            return None
        response = requests.get(url, timeout=10)
        if not hasattr(response, "text"):
            return None
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
    def __init__(self, storage_file: str = "default.db"):
        self.storage_file = storage_file
        self._records = {}
        self._portfolios = {}
        self._reports = {}
        self._stress_results = {}

    def __call__(self, payload=None, *args, **kwargs):
        if isinstance(payload, dict):
            action = payload.get("action")
            table = payload.get("table", "default")
            portfolio_id = payload.get("portfolio_id")
            if action == "save":
                data = payload.get("data", payload)
                if table not in self._records:
                    self._records[table] = {}
                key = portfolio_id or payload.get("simulation_id") or payload.get("id") or "latest"
                self._records[table][key] = data
                return True
            elif action == "get":
                table_records = self._records.get(table, {})
                key = portfolio_id or payload.get("simulation_id") or payload.get("id") or "latest"
                return table_records.get(key)
        return None

    def fetch_portfolio(self, portfolio_id: str):
        if portfolio_id in self._portfolios:
            return self._portfolios[portfolio_id]
        return {
            "portfolio_id": portfolio_id,
            "initial_value": 100000.0,
            "volatility": 0.2,
            "drift": 0.0
        }

    def save_portfolio(self, portfolio_id: str, data: dict):
        self._portfolios[portfolio_id] = data

    def save_report(self, report: dict):
        report_id = report.get("report_id")
        if report_id:
            self._reports[report_id] = report

    def get_report(self, report_id: str):
        return self._reports.get(report_id)

    def get_report_stream(self, report_id: str):
        report = self.get_report(report_id) or {}
        content = json.dumps(report).encode("utf-8")
        return io.BytesIO(content)

    def save_stress_test_result(self, simulation_id: str, result_data: dict) -> bool:
        self._stress_results[simulation_id] = result_data
        return True

    def get_stress_test_result(self, simulation_id: str) -> dict:
        return self._stress_results.get(simulation_id, {})


DbStorage = DBStorage
db_storage = DBStorage()

save_stress_test_result = db_storage.save_stress_test_result
get_stress_test_result = db_storage.get_stress_test_result
fetch_portfolio = db_storage.fetch_portfolio
save_report = db_storage.save_report
get_report_stream = db_storage.get_report_stream
