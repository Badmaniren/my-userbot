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
        if not requests:
            return 0.0
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("price")

    def parse_html_prices(self, url: str):
        if not requests or not BeautifulSoup:
            return None
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find()
        if element and element.text:
            try:
                return float(element.text)
            except ValueError:
                return None
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
    def __init__(self, storage_file="storage.db"):
        self.storage_file = storage_file
        self.registry = {}

    def save(self, key, value):
        self.registry[key] = value
        return True

    def get(self, key, default=None):
        return self.registry.get(key, default)

    def save_alert(self, alert_data):
        return self.save("alert", alert_data)

    def log_error(self, error_data):
        return self.save("error", error_data)

    def persist(self, record_id, payload):
        return self.save(record_id, payload)

    def __call__(self, payload=None, *args, **kwargs):
        if isinstance(payload, dict):
            key = payload.get("action") or payload.get("portfolio_id") or "default_record"
            self.save(key, payload)
            return {"status": "success", "record_id": key, "payload": payload}
        elif isinstance(payload, str):
            return self.get(payload)
        return {"status": "success", "payload": payload}


def db_storage(payload=None, *args, **kwargs):
    if isinstance(payload, dict):
        key = payload.get("action") or payload.get("portfolio_id") or "default_record"
        _db_storage_instance.save(key, payload)
        return {"status": "success", "record_id": key, "payload": payload}
    elif isinstance(payload, str):
        return _db_storage_instance.get(payload)
    return {"status": "success", "payload": payload}


_db_storage_instance = DBStorage()
db_storage.save = _db_storage_instance.save
db_storage.get = _db_storage_instance.get
db_storage.persist = _db_storage_instance.persist
db_storage.save_alert = _db_storage_instance.save_alert
db_storage.log_error = _db_storage_instance.log_error

DbStorage = DBStorage
