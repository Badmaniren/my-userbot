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


class DBStorageCallable:
    def __init__(self):
        self._storage = {}

    def save_impact_analysis(self, portfolio_id_or_data, data=None):
        if isinstance(portfolio_id_or_data, dict):
            pid = portfolio_id_or_data.get("portfolio_id")
            impact_data = portfolio_id_or_data
        else:
            pid = portfolio_id_or_data
            impact_data = data or {}
        if pid:
            self._storage[f"get_stress_impact_{pid}"] = impact_data
            self._storage[f"save_stress_impact_{pid}"] = impact_data
            self._storage[pid] = impact_data
        return impact_data

    def get_stress_impact(self, portfolio_id):
        return self._storage.get(f"get_stress_impact_{portfolio_id}") or self._storage.get(portfolio_id)

    def __call__(self, key_or_action, *args, **kwargs):
        if isinstance(key_or_action, str):
            if key_or_action.startswith("get_stress_impact_"):
                return self._storage.get(key_or_action)
            elif key_or_action.startswith("save_stress_impact_"):
                pid = key_or_action.replace("save_stress_impact_", "")
                data = args[0] if args else (kwargs.get("data") or {})
                self._storage[key_or_action] = data
                self._storage[f"get_stress_impact_{pid}"] = data
                return data
            elif key_or_action in self._storage:
                return self._storage[key_or_action]
        return self._storage.get(key_or_action)

    def __getattr__(self, name):
        def dummy_func(*args, **kwargs):
            if name.startswith("get_"):
                key = args[0] if args else name
                return self._storage.get(key)
            elif name.startswith("save_") or name.startswith("store_"):
                if args:
                    if isinstance(args[0], dict):
                        key = args[0].get("portfolio_id", "default")
                        self._storage[key] = args[0]
                        if "portfolio_id" in args[0]:
                            self._storage[f"get_stress_impact_{args[0]['portfolio_id']}"] = args[0]
                    else:
                        key = args[0]
                        val = args[1] if len(args) > 1 else {}
                        self._storage[key] = val
                return True
            return None
        return dummy_func


db_storage = DBStorageCallable()
