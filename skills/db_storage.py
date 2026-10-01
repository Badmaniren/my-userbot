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
            return None
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
    def __init__(self):
        self._store = {}
        self._in_memory_db = {}

    def __call__(self, payload=None, *args, **kwargs):
        if isinstance(payload, dict):
            action = payload.get("action")
            key = payload.get("key")
            if action == "set":
                val = payload.get("value")
                self._store[key] = val
                return val
            elif action == "get":
                return self._store.get(key)
        return self._store

    def save(self, key, value):
        self._store[key] = value

    def get(self, key):
        return self._store.get(key)

    def save_dashboard(self, results):
        if isinstance(results, dict):
            key = results.get("report_id") or results.get("portfolio_id")
            if key:
                self._store[key] = results
        return True

    def fetch_portfolio(self, portfolio_id):
        return self._in_memory_db.get(portfolio_id, {"portfolio_id": portfolio_id, "initial_value": 100000.0, "volatility": 0.2, "drift": 0.0})

    def save_portfolio(self, portfolio_id, data):
        self._in_memory_db[portfolio_id] = data

    def save_portfolio_position(self, portfolio_id, position):
        self._in_memory_db[f"pos_{portfolio_id}"] = position

    def save_record(self, key, record):
        self._store[key] = record

    def get_record(self, key):
        return self._store.get(key)

    def get_portfolio(self, portfolio_id):
        return self.fetch_portfolio(portfolio_id)

    def load_portfolio(self, portfolio_id):
        return self.fetch_portfolio(portfolio_id)

    def persist_state(self, portfolio_id, state):
        self._in_memory_db[f"state_{portfolio_id}"] = state

    def load_state(self, portfolio_id):
        return self._in_memory_db.get(f"state_{portfolio_id}")

    def fetch_stream(self, portfolio_id):
        return None


DbStorage = DBStorage
db_storage = DBStorage()
DatabaseConnection = DBStorage

_in_memory_db = db_storage._in_memory_db


def save_portfolio_state(portfolio_id, state):
    db_storage.persist_state(portfolio_id, state)


def get_portfolio_state(portfolio_id):
    return db_storage.load_state(portfolio_id)


def save_to_db(key, data):
    db_storage.save(key, data)


def fetch_from_db(key):
    return db_storage.get(key)


def save_report_to_db(key, report):
    db_storage.save(key, report)


def get_report_from_db(key):
    return db_storage.get(key)


def save_macro_evaluation(portfolio_id, evaluation):
    db_storage.save(f"macro_{portfolio_id}", evaluation)


def get_macro_evaluation(portfolio_id):
    return db_storage.get(f"macro_{portfolio_id}")


def save_portfolio_data(portfolio_id, data):
    db_storage.save_portfolio(portfolio_id, data)


def get_portfolio_data(portfolio_id):
    return db_storage.fetch_portfolio(portfolio_id)


def save_simulation_results(sim_id, results):
    db_storage.save(sim_id, results)


def get_simulation_results(sim_id):
    return db_storage.get(sim_id)


def save_portfolio_risk_metrics(portfolio_id, metrics):
    db_storage.save(f"metrics_{portfolio_id}", metrics)


def get_portfolio_risk_metrics(portfolio_id):
    return db_storage.get(f"metrics_{portfolio_id}")


def fetch_portfolio(portfolio_id):
    return db_storage.fetch_portfolio(portfolio_id)


def save_stress_test_result(simulation_id, result_data):
    db_storage.save(simulation_id, result_data)


def get_stress_test_result(simulation_id):
    return db_storage.get(simulation_id)


def fetch_stream(portfolio_id):
    return db_storage.fetch_stream(portfolio_id)


def save_dashboard(results):
    return db_storage.save_dashboard(results)
