import sqlite3
import logging

logger = logging.getLogger("DBStorage")

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
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            return data.get("price")
        except Exception as e:
            logger.error("Failed to fetch price in DBStorage MarketParser from %s: %s", url, e)
            return None

    def parse_html_prices(self, url: str):
        if requests is None or BeautifulSoup is None:
            return None
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            element = soup.find()
            if element and element.text:
                return float(element.text)
            return None
        except Exception as e:
            logger.error("Failed to parse html prices in DBStorage MarketParser from %s: %s", url, e)
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


class DatabaseConnection:
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)


class DBStorage:
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self._registry = {}

    def save(self, key, value):
        self._registry[key] = value

    def get(self, key, default=None):
        return self._registry.get(key, default)

    def fetch_stream(self, stream_id):
        return self._registry.get(stream_id)

    def save_stress_results(self, metrics):
        self._registry["stress_results"] = metrics
        return True

    def save_portfolio_position(self, portfolio_id, position):
        self._registry[f"pos_{portfolio_id}"] = position
        return True

    def save_record(self, record_id, record):
        self._registry[record_id] = record
        return True

    def get_record(self, record_id):
        return self._registry.get(record_id)

    def get_portfolio(self, portfolio_id):
        return self._registry.get(portfolio_id)

    def save_portfolio(self, portfolio_id, data=None):
        if data is None and isinstance(portfolio_id, dict):
            data = portfolio_id
            portfolio_id = data.get("portfolio_id")
        self._registry[portfolio_id] = data
        return True

    def load_portfolio(self, portfolio_id):
        return self._registry.get(portfolio_id)

    def persist_state(self, state):
        self._registry["state"] = state
        return True

    def load_state(self):
        return self._registry.get("state")

    def load_data(self, filename: str):
        parser = MarketParser(filename)
        return parser.load_data(filename)

    def save_sentiment_record(self, record):
        self._registry["sentiment"] = record
        return True

    def export_to_file(self, pid, path):
        with open(path, "w") as f:
            f.write(str(self._registry.get(pid, "")))

    def __call__(self, *args, **kwargs):
        return self


DbStorage = DBStorage
db_storage = DBStorage()


def save_portfolio_state(portfolio_id, state=None):
    return db_storage.save_portfolio(portfolio_id, state)


def get_portfolio_state(portfolio_id):
    return db_storage.get_portfolio(portfolio_id)


def save_to_db(key, data):
    return db_storage.save(key, data)


def fetch_from_db(key):
    return db_storage.get(key)


def save_report_to_db(report_id, report):
    return db_storage.save_record(report_id, report)


def get_report_from_db(report_id):
    return db_storage.get_record(report_id)


def save_macro_evaluation(portfolio_id, evaluation):
    return db_storage.save(f"macro_{portfolio_id}", evaluation)


def get_macro_evaluation(portfolio_id):
    return db_storage.get(f"macro_{portfolio_id}")


def save_portfolio_data(portfolio_id, data):
    return db_storage.save_portfolio(portfolio_id, data)


def get_portfolio_data(portfolio_id):
    return db_storage.get_portfolio(portfolio_id)


def save_simulation_results(sim_id, results):
    return db_storage.save_record(sim_id, results)


def get_simulation_results(sim_id):
    return db_storage.get_record(sim_id)


def save_portfolio_risk_metrics(portfolio_id, metrics):
    return db_storage.save(f"risk_{portfolio_id}", metrics)


def get_portfolio_risk_metrics(portfolio_id):
    return db_storage.get(f"risk_{portfolio_id}")


def fetch_portfolio(portfolio_id):
    return db_storage.get_portfolio(portfolio_id)


def save_stress_test_result(simulation_id, result_data):
    return db_storage.save_record(simulation_id, result_data)


def get_stress_test_result(simulation_id):
    return db_storage.get_record(simulation_id)