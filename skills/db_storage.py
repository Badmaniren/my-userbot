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

    def health_check(self):
        return {"status": "ok"}

    def health_pulse(self, *args, **kwargs):
        return {"status": "ok"}

    def fetch_price(self, url: str):
        if not requests:
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
        if not requests or not BeautifulSoup:
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


class DBStorage:
    def __init__(self):
        self._data = {}

    def __call__(self, *args, **kwargs):
        if kwargs.get("action") == "set":
            key = kwargs.get("record_id") or kwargs.get("key")
            if key:
                self._data[key] = kwargs.get("data")
            return kwargs.get("record_id")
        return self._data

    def fetch_historical_data(self, portfolio_id=None):
        return self._data.get(f"hist_{portfolio_id}", [])

    def fetch_portfolio(self, portfolio_id):
        return self._data.get(portfolio_id, {"portfolio_id": portfolio_id})

    def save_audit_result(self, audit_id, payload):
        self._data[audit_id] = payload
        return True

    def get_audit_result(self, audit_id):
        return self._data.get(audit_id)

    def save_audit_record(self, audit_id, record):
        self._data[audit_id] = record
        return True

    def fetch_audit_record(self, audit_id):
        return self._data.get(audit_id)

    def get_audit_record(self, audit_id):
        return self._data.get(audit_id)

    def fetch_audit(self, audit_id):
        return self._data.get(audit_id)

    def save(self, key, data=None):
        if data is None and isinstance(key, dict):
            self._data.update(key)
        else:
            self._data[key] = data
        return True

    def load(self, target):
        return self._data.get(target)

    def get_health_metrics(self, portfolio_id=None):
        return {"status": "ok"}


DbStorage = DBStorage
db_storage = DBStorage()

_audit_records = {}


def save_audit_result(audit_id, payload):
    _audit_records[audit_id] = payload
    return db_storage.save_audit_result(audit_id, payload)


def get_audit_result(audit_id):
    return db_storage.get_audit_result(audit_id) or _audit_records.get(audit_id)


def db_storage_save(storage_target, data):
    return db_storage.save(storage_target, data)


def db_storage_load(storage_target):
    return db_storage.load(storage_target)


def db_storage_get(storage_target):
    return db_storage.load(storage_target)


def save_audit_record(audit_id, record):
    _audit_records[audit_id] = record
    return db_storage.save_audit_record(audit_id, record)


def fetch_audit_record(audit_id):
    return db_storage.fetch_audit_record(audit_id) or _audit_records.get(audit_id)


def get_audit_record(audit_id):
    return db_storage.get_audit_record(audit_id) or _audit_records.get(audit_id)
