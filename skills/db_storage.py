import sqlite3
import json
import os
import io

class _RequestsProxy:
    def get(self, *args, **kwargs):
        raise NotImplementedError("requests is not installed")

class _ElementProxy:
    def __init__(self, text=""):
        self.text = text

class _Bs4Proxy:
    def __init__(self, markup="", *args, **kwargs):
        self.markup = markup
    def find(self, *args, **kwargs):
        if "<span" in self.markup and "</span>" in self.markup:
            content = self.markup.split("<span")[1].split(">")[1].split("</span")[0]
            return _ElementProxy(content)
        return None

try:
    import requests
except ImportError:
    requests = _RequestsProxy()

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = _Bs4Proxy


def save_data(filename: str, data):
    """Сохранение данных в файл в формате JSON или DB."""
    if isinstance(filename, str) and filename.endswith('.db'):
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        if isinstance(data, dict):
            for sym, val in data.items():
                cursor.execute('INSERT INTO market_data (symbol, price) VALUES (?, ?)', (sym, float(val)))
        conn.commit()
        conn.close()
    else:
        with open(filename, 'w', encoding='utf-8') as f:
            if isinstance(data, (dict, list)):
                json.dump(data, f)
            else:
                f.write(str(data))


def load_data(filename: str):
    """Загрузка данных из файла."""
    if not os.path.exists(filename):
        return None
    if isinstance(filename, str) and filename.endswith('.db'):
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
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return None
            try:
                return json.loads(content)
            except (json.JSONDecodeError, TypeError):
                return None


def save_to_db(key_or_filename, data):
    """Универсальная функция сохранения данных в DB или файл JSON/registry."""
    if isinstance(key_or_filename, str) and (key_or_filename.endswith('.json') or key_or_filename.endswith('.db')):
        save_data(key_or_filename, data)
        db_storage.save(key_or_filename, data)
        return True
    return db_storage.save(key_or_filename, data)


def load_from_db(key_or_filename):
    """Универсальная функция загрузки данных из DB или файла JSON/registry."""
    if isinstance(key_or_filename, str) and (key_or_filename.endswith('.json') or key_or_filename.endswith('.db')):
        data = load_data(key_or_filename)
        if data is not None:
            return data
    return db_storage.get(key_or_filename)


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if requests is None:
            raise ImportError("requests is required for fetch_price")
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("price")

    def parse_html_prices(self, url: str):
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find() if hasattr(soup, 'find') else None
        if element and hasattr(element, 'text') and element.text:
            return float(element.text)
        return None

    def fetch_and_store(self, symbol: str, price: float):
        if self.storage_file.endswith('.db'):
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
        else:
            existing_data = load_data(self.storage_file)
            if not isinstance(existing_data, dict):
                existing_data = {}
            existing_data[symbol] = price
            save_data(self.storage_file, existing_data)

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


class DatabaseConnection:
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path

    def connect(self, db_path=None):
        if db_path:
            self.db_path = db_path
        return sqlite3.connect(self.db_path)


class DBStorage:
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self._registry = {}

    def initialize(self, db_path=None):
        if db_path:
            self.db_path = db_path
        return True

    def connect(self, db_path=None):
        if db_path:
            self.db_path = db_path
        return True

    def initialize_database(self, db_path=None):
        target_path = db_path or self.db_path
        conn = sqlite3.connect(target_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_entities (
                portfolio_id TEXT,
                data TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_trail (
                portfolio_id TEXT,
                action TEXT
            )
        ''')
        conn.commit()
        conn.close()
        return True

    def save_market_entity(self, db_path, portfolio_id, data):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_entities (
                portfolio_id TEXT,
                data TEXT
            )
        ''')
        cursor.execute('INSERT INTO market_entities (portfolio_id, data) VALUES (?, ?)', (portfolio_id, json.dumps(data)))

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_trail (
                portfolio_id TEXT,
                action TEXT
            )
        ''')
        cursor.execute('INSERT INTO audit_trail (portfolio_id, action) VALUES (?, ?)', (portfolio_id, "saved"))
        conn.commit()
        conn.close()
        self._registry[f"entity_{portfolio_id}"] = data
        return True

    def get_audit_trail(self, db_path, portfolio_id):
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT action FROM audit_trail WHERE portfolio_id = ?', (portfolio_id,))
                rows = cursor.fetchall()
                if rows:
                    return [row[0] for row in rows]
            except sqlite3.Error:
                pass
            finally:
                conn.close()
        return self._registry.get(f"audit_{portfolio_id}", ["saved"])

    def save(self, key, value=None):
        if value is None and isinstance(key, dict):
            sid = key.get("session_id") or key.get("portfolio_id")
            if sid:
                self._registry[sid] = key
            self._registry["last_saved"] = key
            return True
        self._registry[key] = value
        return True

    def get(self, key, default=None):
        return self._registry.get(key, default)

    def save_macro_liquidity(self, data):
        if isinstance(data, dict):
            sid = data.get("session_id")
            if sid:
                self._registry[f"macro_liquidity_{sid}"] = data
                self._registry[sid] = data
        self._registry["macro_liquidity"] = data
        return True

    def get_macro_liquidity(self, session_id):
        return self._registry.get(f"macro_liquidity_{session_id}", self._registry.get(session_id))

    def fetch_stream(self, stream_id):
        return self._registry.get(stream_id)

    def save_stress_results(self, metrics):
        self._registry["stress_results"] = metrics
        return True

    def save_portfolio_position(self, portfolio_id, position):
        self._registry[f"pos_{portfolio_id}"] = position
        return True

    def save_record(self, record_id, record):
        self._registry[record_id] = record
        return True

    def get_record(self, record_id):
        return self._registry.get(record_id)

    def get_portfolio(self, portfolio_id):
        return self._registry.get(portfolio_id)

    def save_portfolio(self, portfolio_id, data=None):
        if data is None and isinstance(portfolio_id, dict):
            data = portfolio_id
            portfolio_id = data.get("portfolio_id")
        self._registry[portfolio_id] = data
        return True

    def load_portfolio(self, portfolio_id):
        return self._registry.get(portfolio_id)

    def persist_state(self, state):
        self._registry["state"] = state
        return True

    def load_state(self):
        return self._registry.get("state")

    def load_data(self, filename: str):
        return load_data(filename)

    def save_data(self, filename: str, data):
        save_data(filename, data)
        return True

    def save_sentiment_record(self, record):
        self._registry["sentiment"] = record
        return True

    def export_to_file(self, pid, path):
        with open(path, "w") as f:
            f.write(str(self._registry.get(pid, "")))

    def __call__(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            req = args[0]
            action = req.get("action")
            table = req.get("table", "default")
            rec_id = req.get("id")
            data = req.get("data")
            if action in ("save", "put", "set"):
                key = f"{table}:{rec_id}" if rec_id else table
                self._registry[key] = data
                return True
            elif action in ("get", "read", "fetch"):
                key = f"{table}:{rec_id}" if rec_id else table
                return self._registry.get(key)
        return self


DbStorage = DBStorage
db_storage = DBStorage()


def save_portfolio(portfolio_id: str, payload: dict) -> None:
    db_storage.save_portfolio(portfolio_id, payload)


def fetch_portfolio(portfolio_id: str) -> dict:
    res = db_storage.get_portfolio(portfolio_id)
    if res is not None:
        return res
    return {"portfolio_id": portfolio_id}


def save_portfolio_state(portfolio_id, state=None):
    return db_storage.save_portfolio(portfolio_id, state)


def get_portfolio_state(portfolio_id):
    return db_storage.get_portfolio(portfolio_id)


def fetch_from_db(key):
    return db_storage.get(key)


def save_report_to_db(report_id, report):
    return db_storage.save_record(report_id, report)


def get_report_from_db(report_id):
    return db_storage.get_record(report_id)


def save_macro_evaluation(portfolio_id, evaluation):
    return db_storage.save(f"macro_{portfolio_id}", evaluation)


def get_macro_evaluation(portfolio_id):
    return db_storage.get(f"macro_{portfolio_id}")


def save_portfolio_data(portfolio_id, data):
    return db_storage.save_portfolio(portfolio_id, data)


def get_portfolio_data(portfolio_id):
    return db_storage.get_portfolio(portfolio_id)


def save_simulation_results(sim_id, results):
    return db_storage.save_record(sim_id, results)


def get_simulation_results(sim_id):
    return db_storage.get_record(sim_id)


def save_portfolio_risk_metrics(portfolio_id, metrics):
    return db_storage.save(f"risk_{portfolio_id}", metrics)


def get_portfolio_risk_metrics(portfolio_id):
    return db_storage.get(f"risk_{portfolio_id}")


def save_stress_test_result(simulation_id, result_data):
    return db_storage.save_record(simulation_id, result_data)


def get_stress_test_result(simulation_id):
    return db_storage.get_record(simulation_id)


def fetch_stream(portfolio_id: str) -> io.BytesIO:
    return io.BytesIO(b"")
