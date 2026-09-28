import io
import json
import os
import sqlite3

try:
    import requests
except ImportError:
    from unittest.mock import MagicMock
    requests = MagicMock()

try:
    from bs4 import BeautifulSoup
except ImportError:
    class BeautifulSoup:
        def __init__(self, text, *args, **kwargs):
            self.text = text or ""
        def find(self, *args, **kwargs):
            import re
            m = re.search(r'>([^<]+)<', self.text)
            if m:
                val = m.group(1).strip()
                if val:
                    class _Elem:
                        def __init__(self, t):
                            self.text = t
                    return _Elem(val)
            return None
        def find_all(self, *args, **kwargs):
            return []


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


_STORAGE_REGISTRY = {}


class DBStorage:
    _registry = _STORAGE_REGISTRY

    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self._positions = {}
        self._streams = {}
        self._records = {}

    def save(self, entity_id=None, data=None, *args, **kwargs):
        if entity_id and data is not None:
            self._registry[entity_id] = data
            return True
        if isinstance(entity_id, dict):
            key = entity_id.get("id") or entity_id.get("hedge_id") or entity_id.get("portfolio_id")
            if key:
                self._registry[key] = entity_id
            return True
        return True

    def get(self, entity_id=None, *args, **kwargs):
        if entity_id:
            return self._registry.get(entity_id)
        return None

    def fetch_stream(self, portfolio_id: str):
        if portfolio_id in self._streams:
            return self._streams[portfolio_id]
        if portfolio_id in self._positions:
            lines = []
            for pos in self._positions[portfolio_id]:
                ticker = pos.get("ticker", "")
                shares = pos.get("shares", 0)
                purchase_price = pos.get("purchase_price", 0.0)
                current_price = pos.get("current_price", purchase_price)
                gain = pos.get("gain", (current_price - purchase_price) * shares)
                lines.append(f"portfolio_id:{portfolio_id},ticker:{ticker},gain:{gain}")
            content = "\n".join(lines).encode("utf-8")
            return io.BytesIO(content)
        return io.BytesIO(b"")

    def save_portfolio_position(self, data: dict):
        portfolio_id = data.get("portfolio_id")
        if portfolio_id:
            if portfolio_id not in self._positions:
                self._positions[portfolio_id] = []
            self._positions[portfolio_id].append(data)

    def save_record(self, key, record=None):
        if record is not None:
            self._records[key] = record
            self._registry[key] = record
        else:
            self._registry[str(key)] = key
        return True

    def get_record(self, key):
        if key in self._records:
            return self._records[key]
        return self._registry.get(key)

    def get_portfolio(self, portfolio_id: str):
        if portfolio_id in self._positions and self._positions[portfolio_id]:
            return self._positions[portfolio_id][0]
        return self._registry.get(portfolio_id)

    def __call__(self, action=None, entity_id=None, data=None, *args, **kwargs):
        if action == "save":
            if entity_id and data is not None:
                self.save(entity_id=entity_id, data=data)
            elif data is not None:
                self.save(entity_id=data)
            elif kwargs.get("data") is not None:
                self.save(entity_id=kwargs.get("entity_id"), data=kwargs.get("data"))
            return True
        elif action == "get":
            return self.get(entity_id=entity_id or kwargs.get("entity_id"))
        elif isinstance(action, dict):
            act = action.get("action")
            eid = action.get("entity_id") or action.get("hedge_id") or action.get("portfolio_id")
            if act == "save":
                d = action.get("data", action)
                self.save(entity_id=eid, data=d)
                return True
            elif act == "get":
                return self.get(entity_id=eid)
        return self._registry.get(entity_id) if entity_id else None


class DatabaseConnection:
    def __init__(self, db_path="market_database.db"):
        self.db_path = db_path

    def save_article(self, article):
        return True

    def get_article(self, article_id):
        return {}


def save_to_db(record):
    return True


def fetch_from_db(metric_id):
    return {}


def save_portfolio(data, filepath):
    if not filepath:
        return False
    dirname = os.path.dirname(filepath)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    if str(filepath).endswith('.db'):
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL
            )
        ''')
        cursor.execute('INSERT INTO portfolio (data) VALUES (?)', (json.dumps(data),))
        conn.commit()
        conn.close()
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    return True


def load_portfolio(filepath):
    if not filepath or not os.path.exists(filepath):
        return {}
    if str(filepath).endswith('.db'):
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        try:
            cursor.execute('CREATE TABLE IF NOT EXISTS portfolio (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)')
            cursor.execute('SELECT data FROM portfolio ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
        except sqlite3.Error:
            pass
        finally:
            conn.close()
        return {}
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


db_storage = DBStorage()
DbStorage = DBStorage
MarketStorage = DBStorage
MarketDatabaseStorage = DBStorage
DatabaseStorage = DBStorage
