import sqlite3
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
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


class DBStorage:
    def __init__(self, **kwargs):
        self._records = {}

    def save(self, data):
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    key = item.get("audit_id") or item.get("id") or item.get("tag")
                    if key:
                        self._records[key] = item
        elif isinstance(data, dict):
            key = data.get("audit_id") or data.get("id") or data.get("tag")
            if key:
                self._records[key] = data
        return True

    def save_record(self, key, value):
        self._records[key] = value

    def get_record(self, key):
        return self._records.get(key)


DbStorage = DBStorage


def save(data):
    if not hasattr(save, "_records"):
        save._records = {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                key = item.get("audit_id") or item.get("id") or item.get("tag")
                if key:
                    save._records[key] = item
    elif isinstance(data, dict):
        key = data.get("audit_id") or data.get("id") or data.get("tag")
        if key:
            save._records[key] = data
    return True
