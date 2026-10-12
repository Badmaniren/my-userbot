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
        try:
            data = response.json()
        except Exception:
            return None
        if isinstance(data, dict):
            return data.get("price")
        return None

    def parse_html_prices(self, url: str):
        if requests is None or BeautifulSoup is None:
            return None
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find()
        if element and element.text:
            try:
                return float(element.text)
            except (ValueError, TypeError):
                return None
        return None

    def fetch_and_store(self, symbol: str, price: float):
        if not isinstance(symbol, str) or not isinstance(price, (int, float)) or isinstance(price, bool):
            raise TypeError("Строгая типизация нарушена: symbol должен быть str, а price — числом.")
        
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
            (symbol, float(price))
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


class DbStorage:
    def __init__(self):
        self._records = {}
        self._audit_results = {}
        self._storage_data = {}

    def fetch_portfolio_matrix_params(self, portfolio_id: str, scenario_code: str) -> dict:
        return {"weight": 1.0, "health_base": 100.0}

    def fetch_portfolio(self, portfolio_id: str) -> dict:
        return {"portfolio_id": portfolio_id, "initial_value": 100000.0, "volatility": 0.2, "drift": 0.0}

    def save(self, key, value):
        self._records[key] = value

    def save_audit_result(self, audit_id: str, payload: dict):
        self._audit_results[audit_id] = payload

    def get_audit_result(self, audit_id: str):
        return self._audit_results.get(audit_id)

    def db_storage_save(self, storage_target: str, data):
        self._storage_data[storage_target] = data

    def db_storage_load(self, storage_target: str):
        return self._storage_data.get(storage_target)

    def db_storage_get(self, storage_target: str):
        return self._storage_data.get(storage_target)

    def save_audit_record(self, audit_id: str, record):
        self._records[audit_id] = record

    def fetch_audit_record(self, audit_id: str):
        return self._records.get(audit_id)

    def get_audit_record(self, audit_id: str):
        return self._records.get(audit_id)

    def health_check(self) -> bool:
        return True

    def health_pulse(self, *args, **kwargs) -> bool:
        return True


DBStorage = DbStorage
db_storage = DbStorage()

def fetch_portfolio_matrix_params(portfolio_id: str, scenario_code: str) -> dict:
    return db_storage.fetch_portfolio_matrix_params(portfolio_id, scenario_code)

def fetch_portfolio(portfolio_id: str) -> dict:
    return db_storage.fetch_portfolio(portfolio_id)

def save_audit_result(audit_id: str, payload: dict):
    return db_storage.save_audit_result(audit_id, payload)

def get_audit_result(audit_id: str):
    return db_storage.get_audit_result(audit_id)

def db_storage_save(storage_target: str, data):
    return db_storage.db_storage_save(storage_target, data)

def db_storage_load(storage_target: str):
    return db_storage.db_storage_load(storage_target)

def db_storage_get(storage_target: str):
    return db_storage.db_storage_get(storage_target)

def save_audit_record(audit_id: str, record):
    return db_storage.save_audit_record(audit_id, record)

def fetch_audit_record(audit_id: str):
    return db_storage.fetch_audit_record(audit_id)

def get_audit_record(audit_id: str):
    return db_storage.get_audit_record(audit_id)
