import sqlite3
try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class DatabaseConnection:
    def __init__(self, db_path="market_data.db"):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)


class DBStorage:
    def __init__(self, db_path="market_data.db"):
        self.db_path = db_path
        self._store = {}

    def __call__(self, payload=None, *args, **kwargs):
        if isinstance(payload, dict):
            action = payload.get("action")
            table = payload.get("table", "default")
            record_id = payload.get("id")
            data = payload.get("data")
            if action == "set":
                key = f"{table}:{record_id}" if record_id else table
                self._store[key] = data
                return data
            elif action == "get":
                key = f"{table}:{record_id}" if record_id else table
                return self._store.get(key)
        return self._store

    def save(self, key, value):
        self._store[key] = value

    def get(self, key, default=None):
        return self._store.get(key, default)

    def fetch_stream(self, key=None):
        return self._store.get(key)

    def save_portfolio_position(self, portfolio_id, position):
        self._store[f"position:{portfolio_id}"] = position

    def save_record(self, record_id, record):
        self._store[f"record:{record_id}"] = record

    def get_record(self, record_id):
        return self._store.get(f"record:{record_id}")

    def get_portfolio(self, portfolio_id):
        return self._store.get(f"portfolio:{portfolio_id}", {})

    def save_portfolio(self, portfolio_id, data):
        self._store[f"portfolio:{portfolio_id}"] = data

    def load_portfolio(self, portfolio_id_or_file):
        return self._store.get(f"portfolio:{portfolio_id_or_file}", {})

    def persist_state(self, key, state):
        self._store[f"state:{key}"] = state

    def load_state(self, key):
        return self._store.get(f"state:{key}")


DbStorage = DBStorage
db_storage = DBStorage()


def save_portfolio_state(portfolio_id, state):
    db_storage.save_portfolio(portfolio_id, state)

def get_portfolio_state(portfolio_id):
    return db_storage.get_portfolio(portfolio_id)

def save_to_db(key, value):
    db_storage.save(key, value)

def fetch_from_db(key):
    return db_storage.get(key)

def save_report_to_db(report_id, report):
    db_storage.save_record(f"report:{report_id}", report)

def get_report_from_db(report_id):
    return db_storage.get_record(f"report:{report_id}")

def save_macro_evaluation(portfolio_id, evaluation):
    db_storage.save_record(f"macro:{portfolio_id}", evaluation)

def get_macro_evaluation(portfolio_id):
    return db_storage.get_record(f"macro:{portfolio_id}")

def save_portfolio_data(portfolio_id, data):
    db_storage.save_portfolio(portfolio_id, data)

def get_portfolio_data(portfolio_id):
    return db_storage.get_portfolio(portfolio_id)

def save_simulation_results(sim_id, results):
    db_storage.save_record(f"sim:{sim_id}", results)

def get_simulation_results(sim_id):
    return db_storage.get_record(f"sim:{sim_id}")


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