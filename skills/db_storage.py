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

    def fetch_price(self, url: str, symbol: str = None):
        if requests is None:
            return 100.0
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            return data.get("price", 100.0)
        except Exception:
            return 100.0

    def parse_html_prices(self, url: str):
        if requests is None or BeautifulSoup is None:
            return None
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            element = soup.find()
            if element and element.text:
                return float(element.text)
        except Exception:
            pass
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


_storage_data = {}
_stress_test_results = {}
_portfolio_db = {}


class DBStorage:
    def __init__(self, storage_file: str = "default.db"):
        self.storage_file = storage_file

    def save(self, key: str, value):
        _storage_data[key] = value

    def get(self, key: str, default=None):
        return _storage_data.get(key, default)

    def __call__(self, key: str = None):
        if key:
            return self.get(key)
        return _storage_data

    def fetch_stream(self, key: str = None):
        return _storage_data.get(key)

    def save_portfolio_position(self, portfolio_id: str, position: dict):
        if portfolio_id not in _portfolio_db:
            _portfolio_db[portfolio_id] = {}
        _portfolio_db[portfolio_id].update(position)

    def save_record(self, record_id: str, data: dict):
        _storage_data[record_id] = data

    def get_record(self, record_id: str):
        return _storage_data.get(record_id)

    def get_portfolio(self, portfolio_id: str):
        return fetch_portfolio(portfolio_id)

    def save_portfolio(self, portfolio_id: str, data: dict):
        _portfolio_db[portfolio_id] = data

    def load_portfolio(self, portfolio_id: str):
        return get_portfolio_data(portfolio_id)

    def persist_state(self, key: str, state: dict):
        _storage_data[key] = state

    def load_state(self, key: str):
        return _storage_data.get(key, {})


DbStorage = DBStorage
db_storage = DBStorage()


class DatabaseConnection:
    def __init__(self, db_path: str = "default.db"):
        self.db_path = db_path

    def execute(self, query: str, params=()):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()


def fetch_portfolio(portfolio_id: str) -> dict:
    if portfolio_id in _portfolio_db:
        return _portfolio_db[portfolio_id]
    return {
        "portfolio_id": portfolio_id,
        "initial_value": 100000.0,
        "volatility": 0.2,
        "drift": 0.01
    }


def save_stress_test_result(simulation_id: str, result_data: dict) -> bool:
    _stress_test_results[simulation_id] = result_data
    return True


def get_stress_test_result(simulation_id: str) -> dict:
    return _stress_test_results.get(simulation_id, {})


def save_portfolio_state(portfolio_id: str, state: dict):
    _portfolio_db[portfolio_id] = state


def get_portfolio_state(portfolio_id: str):
    return fetch_portfolio(portfolio_id)


def save_to_db(key: str, data):
    _storage_data[key] = data


def fetch_from_db(key: str):
    return _storage_data.get(key)


def save_report_to_db(report_id: str, report: dict):
    _storage_data[f"report_{report_id}"] = report


def get_report_from_db(report_id: str):
    return _storage_data.get(f"report_{report_id}")


def save_macro_evaluation(portfolio_id: str, evaluation: dict):
    _storage_data[f"macro_{portfolio_id}"] = evaluation


def get_macro_evaluation(portfolio_id: str):
    return _storage_data.get(f"macro_{portfolio_id}")


def save_portfolio_data(portfolio_id: str, data: dict):
    _portfolio_db[portfolio_id] = data


def get_portfolio_data(portfolio_id: str):
    return fetch_portfolio(portfolio_id)


def save_simulation_results(sim_id: str, results: dict):
    _stress_test_results[sim_id] = results


def get_simulation_results(sim_id: str):
    return _stress_test_results.get(sim_id)


def save_portfolio_risk_metrics(portfolio_id: str, metrics: dict):
    _storage_data[f"risk_{portfolio_id}"] = metrics


def get_portfolio_risk_metrics(portfolio_id: str):
    return _storage_data.get(f"risk_{portfolio_id}")
