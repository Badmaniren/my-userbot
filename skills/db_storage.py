import sqlite3

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

_AUDIT_RECORDS = {}


def save_audit_record(audit_id: str, record: dict) -> bool:
    if not audit_id:
        return False
    _AUDIT_RECORDS[audit_id] = record
    return True


def get_audit_record(audit_id: str) -> dict | None:
    return _AUDIT_RECORDS.get(audit_id)


def fetch_audit_record(audit_id: str) -> dict | None:
    return get_audit_record(audit_id)


class DbStorage:
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path

    def get_portfolio(self, portfolio_id: str) -> dict:
        return {"portfolio_id": portfolio_id, "holdings": [], "status": "active"}

    def fetch_audit(self, audit_id: str) -> dict | None:
        return get_audit_record(audit_id)

    def save(self, payload) -> bool:
        if isinstance(payload, dict) and "audit_id" in payload:
            return save_audit_record(payload["audit_id"], payload)
        return True

    def execute(self, query: str, params=()):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query_upper = query.strip().upper() if isinstance(query, str) else ""
        if query_upper.startswith("SELECT"):
            try:
                cursor.execute(query, params)
                rows = cursor.fetchall()
            except sqlite3.OperationalError:
                rows = []
            conn.close()
            return rows
        else:
            try:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS regulatory_feeds (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_id TEXT
                    )
                ''')
                cursor.execute(query, params)
                conn.commit()
            except Exception:
                pass
            conn.close()
            return True

    def __call__(self, query_or_payload=None, params=(), **kwargs):
        if isinstance(query_or_payload, str):
            return self.execute(query_or_payload, params)
        if isinstance(query_or_payload, dict):
            return self.save(query_or_payload)
        if "key" in kwargs and "value" in kwargs:
            return self.save({"key": kwargs["key"], "value": kwargs["value"]})
        return {"status": "success"}


db_storage = DbStorage()


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if requests is None:
            return None
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
        except Exception:
            return None
        if isinstance(data, dict):
            return data.get("price")
        return None

    def parse_html_prices(self, url: str):
        if requests is None or BeautifulSoup is None:
            return None
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            element = soup.find()
            if element and element.text:
                try:
                    return float(element.text)
                except (ValueError, TypeError):
                    return None
        except Exception:
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
