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
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("price")

    def parse_html_prices(self, url: str):
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


_report_cache = {}


def save_report_to_db(report_id, report_data, storage_file: str = None):
    """Saves a report to the DB/cache."""
    _report_cache[report_id] = report_data
    if storage_file and storage_file.endswith('.db'):
        conn = sqlite3.connect(storage_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                report_id TEXT PRIMARY KEY,
                data TEXT
            )
        ''')
        import json
        cursor.execute(
            'INSERT OR REPLACE INTO reports (report_id, data) VALUES (?, ?)',
            (report_id, json.dumps(report_data))
        )
        conn.commit()
        conn.close()
    return True


def get_report_from_db(report_id, storage_file: str = None):
    """Retrieves a report from the DB/cache."""
    if report_id in _report_cache:
        return _report_cache[report_id]
    if storage_file and storage_file.endswith('.db'):
        conn = sqlite3.connect(storage_file)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT data FROM reports WHERE report_id = ?', (report_id,))
            row = cursor.fetchone()
            if row:
                import json
                return json.loads(row[0])
        finally:
            conn.close()
    return None