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
    def __init__(self):
        self._storage = {}

    def __call__(self, payload: dict):
        if not isinstance(payload, dict):
            return {}
        action = payload.get("action")
        table = payload.get("table", "default")
        portfolio_id = payload.get("portfolio_id") or payload.get("id")

        if action in ("set", "save", "store"):
            data = payload.get("data", payload)
            if table not in self._storage:
                self._storage[table] = {}
            if portfolio_id:
                self._storage[table][portfolio_id] = data
            return data
        elif action in ("get", "load", "fetch"):
            if table in self._storage and portfolio_id in self._storage[table]:
                return self._storage[table][portfolio_id]
            return {"portfolio_id": portfolio_id}
        return {}

    def load_binary_stream(self, portfolio_id, simulations_count=0):
        import io
        import uuid
        return io.BytesIO(uuid.uuid4().bytes + b"\x00" * 32)

    def fetch_portfolio(self, portfolio_id):
        return {"portfolio_id": portfolio_id, "initial_value": 100000.0, "volatility": 0.2, "drift": 0.0}


DbStorage = DBStorage
db_storage = DBStorage()