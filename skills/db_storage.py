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


_STORAGE = {}
_REPORTS = {}


class DBStorageCallable:
    def __init__(self):
        self.storage = _STORAGE

    def __call__(self, record=None, *args, **kwargs):
        action = kwargs.get("action")
        target_id = kwargs.get("target_id") or kwargs.get("portfolio_id") or kwargs.get("key")
        payload = kwargs.get("payload") or kwargs.get("data")

        if action in ("save_prediction", "save", "save_record"):
            if target_id is not None:
                self.storage[f"prediction:{target_id}"] = payload
                self.storage[target_id] = payload
            elif record is not None:
                if isinstance(record, dict):
                    rec_id = record.get("id") or record.get("portfolio_id") or "latest"
                    self.storage[rec_id] = record
            return payload or record
        elif action in ("get_prediction", "get", "get_record"):
            if target_id is not None:
                return self.storage.get(f"prediction:{target_id}") or self.storage.get(target_id)
            return self.storage
        elif record is not None:
            if isinstance(record, dict):
                rec_id = record.get("id") or record.get("portfolio_id") or "latest"
                self.storage[rec_id] = record
            return record
        return self.storage

    def get(self, key, default=None):
        return self.storage.get(key, default)

    def save(self, data):
        return save(data)

    def get_from_database(self, table, key):
        return get_from_database(table, key)

    def save_to_database(self, table, key, value):
        return save_to_database(table, key, value)


db_storage = DBStorageCallable()


def get_from_database(table, key):
    return _STORAGE.get(f"{table}:{key}")


def save_to_database(table, key, value):
    _STORAGE[f"{table}:{key}"] = value
    return True


def save_record(key, data):
    _STORAGE[key] = data
    return data


def get_record(key):
    return _STORAGE.get(key)


def save_audit_record(audit_key, audit_data):
    return save_record(f"audit:{audit_key}", audit_data)


def fetch_audit_record(audit_key):
    return get_record(f"audit:{audit_key}")


def save_portfolio(portfolio_id, data):
    return save_record(f"portfolio:{portfolio_id}", data)


def store_portfolio(portfolio_id, data):
    return save_portfolio(portfolio_id, data)


def fetch_portfolio(portfolio_id, db_path=None):
    res = get_record(f"portfolio:{portfolio_id}") or get_record(portfolio_id)
    if not res and hasattr(db_storage, "_in_memory_db"):
        res = getattr(db_storage, "_in_memory_db", {}).get(portfolio_id)
    if not res:
        res = {"portfolio_id": portfolio_id}
    return res


def save_evaluation_result(record_id, data):
    return save_record(f"eval:{record_id}", data)


def get_evaluation_result(record_id):
    return get_record(f"eval:{record_id}")


def save(data):
    if isinstance(data, dict):
        data_id = data.get("id") or data.get("portfolio_id") or "latest"
        _STORAGE[data_id] = data
    return data


def store_report(data):
    return save_report("report_latest", data)


def save_report(report_id, data):
    _REPORTS[report_id] = data
    return data


def fetch_stored_report(report_id):
    return _REPORTS.get(report_id)


def db_storage_handler(payload):
    return save(payload)


class DBStorage:
    def __init__(self, *args, **kwargs):
        pass

    def connect(self, db_path="market_data.db"):
        return sqlite3.connect(db_path)

    def save_record(self, key, data):
        return save_record(key, data)

    def get_record(self, key):
        return get_record(key)


DbStorage = DBStorage
