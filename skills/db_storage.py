import sqlite3
import uuid

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

_ml_model_metadata = {}
_audit_artifacts = {}


def connect(db_path: str = ":memory:"):
    return True


def fetch_historical_data(target_metric=None):
    return [
        {"metric": target_metric, "val": 0.1},
        {"metric": target_metric, "val": 0.2},
        {"metric": target_metric, "val": 0.3}
    ]


def save_audit_artifact(stream):
    artifact_id = str(uuid.uuid4())
    if hasattr(stream, "read"):
        content = stream.read()
    else:
        content = stream
    _audit_artifacts[artifact_id] = content
    return artifact_id


def save_ml_audit_model_metadata(metadata: dict):
    model_id = metadata.get("model_id") if isinstance(metadata, dict) else None
    if model_id:
        _ml_model_metadata[model_id] = metadata
    return model_id


def get_ml_audit_model_metadata(model_id: str):
    return _ml_model_metadata.get(model_id)


class DBStorage:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path

    def connect(self):
        return connect(self.db_path)

    def fetch_historical_data(self, target_metric=None):
        return fetch_historical_data(target_metric)

    def save_audit_artifact(self, stream):
        return save_audit_artifact(stream)

    def save_ml_audit_model_metadata(self, metadata: dict):
        return save_ml_audit_model_metadata(metadata)

    def get_ml_audit_model_metadata(self, model_id: str):
        return get_ml_audit_model_metadata(model_id)


DbStorage = DBStorage


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
