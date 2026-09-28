import sqlite3
try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if requests is None:
            return 0.0
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("price")

    def parse_html_prices(self, url: str):
        if requests is None or BeautifulSoup is None:
            return None
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
        self.portfolios = {}
        self.hedge_signals = {}
        self.events = []

    def save_portfolio(self, portfolio_id: str, assets: dict):
        self.portfolios[portfolio_id] = assets

    def get_portfolio(self, portfolio_id: str):
        return self.portfolios.get(portfolio_id, {})

    def delete_portfolio(self, portfolio_id: str):
        self.portfolios.pop(portfolio_id, None)

    def save_hedge_signal(self, portfolio_id: str, signal_data: dict):
        if portfolio_id not in self.hedge_signals:
            self.hedge_signals[portfolio_id] = []
        self.hedge_signals[portfolio_id].append(signal_data)

    def get_latest_hedge_signal(self, portfolio_id: str):
        signals = self.hedge_signals.get(portfolio_id, [])
        return signals[-1] if signals else None

    def save_event(self, event_data: dict):
        self.events.append(event_data)