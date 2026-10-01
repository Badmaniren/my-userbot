import sqlite3

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

_in_memory_db = {}


class DBStorage:
    def __init__(self, db_path="default.db"):
        self.db_path = db_path
        self._data = {}

    def save(self, key, value):
        self._data[key] = value
        _in_memory_db[key] = value

    def get(self, key, default=None):
        return self._data.get(key, _in_memory_db.get(key, default))

    def fetch_portfolio(self, portfolio_id):
        return self.get(portfolio_id)

    def save_portfolio(self, portfolio_id, data=None):
        if isinstance(portfolio_id, dict) and data is None:
            data = portfolio_id
            portfolio_id = data.get("portfolio_id", "default")
        self.save(portfolio_id, data)
        return data


DbStorage = DBStorage
db_storage = DBStorage()


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if requests is None:
            raise ImportError("requests is not installed")
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("price")

    def parse_html_prices(self, url: str):
        if requests is None or BeautifulSoup is None:
            raise ImportError("requests or bs4 is not installed")
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


def fetch_portfolio(portfolio_id):
    return _in_memory_db.get(portfolio_id)


def save_portfolio(portfolio_id, data=None):
    if isinstance(portfolio_id, dict) and data is None:
        data = portfolio_id
        portfolio_id = data.get("portfolio_id", "default")
    _in_memory_db[portfolio_id] = data
    return data


def get_portfolio(portfolio_id):
    return fetch_portfolio(portfolio_id)


def save_portfolio_state(portfolio_id, state):
    _in_memory_db[f"state_{portfolio_id}"] = state


def get_portfolio_state(portfolio_id):
    return _in_memory_db.get(f"state_{portfolio_id}")


def save_to_db(key, data):
    _in_memory_db[key] = data


def fetch_from_db(key, default=None):
    return _in_memory_db.get(key, default)


def save_report_to_db(report_id, report):
    _in_memory_db[f"report_{report_id}"] = report


def get_report_from_db(report_id):
    return _in_memory_db.get(f"report_{report_id}")


def save_macro_evaluation(portfolio_id, evaluation):
    _in_memory_db[f"macro_{portfolio_id}"] = evaluation


def get_macro_evaluation(portfolio_id):
    return _in_memory_db.get(f"macro_{portfolio_id}")


def save_portfolio_data(portfolio_id, data):
    _in_memory_db[portfolio_id] = data


def get_portfolio_data(portfolio_id):
    return _in_memory_db.get(portfolio_id)


def save_simulation_results(sim_id, results):
    _in_memory_db[f"sim_{sim_id}"] = results


def get_simulation_results(sim_id):
    return _in_memory_db.get(f"sim_{sim_id}")


def save_portfolio_risk_metrics(portfolio_id, metrics):
    _in_memory_db[f"risk_{portfolio_id}"] = metrics


def get_portfolio_risk_metrics(portfolio_id):
    return _in_memory_db.get(f"risk_{portfolio_id}")


def save_stress_test_result(simulation_id, result_data):
    _in_memory_db[f"stress_{simulation_id}"] = result_data


def get_stress_test_result(simulation_id):
    return _in_memory_db.get(f"stress_{simulation_id}")
