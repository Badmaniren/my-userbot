import sqlite3
from typing import Any, Dict, Union, List

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


_IN_MEMORY_DB: List[Dict[str, Any]] = []


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
    def __call__(self, payload: Union[Dict[str, Any], str] = None, **kwargs: Any) -> Any:
        if isinstance(payload, str):
            return {"status": "ok", "message": payload}
        if not isinstance(payload, dict):
            payload = kwargs

        action = payload.get("action", "").upper()
        table = payload.get("table", "default")
        data = payload.get("data", {})
        filter_query = payload.get("filter", {})

        if action == "INSERT":
            record = {"table": table, "data": data}
            _IN_MEMORY_DB.append(record)
            return {"status": "inserted", "record": record}
        elif action == "SELECT":
            results = []
            for item in _IN_MEMORY_DB:
                if item["table"] == table:
                    match = True
                    for k, v in filter_query.items():
                        if item["data"].get(k) != v:
                            match = False
                            break
                    if match:
                        results.append(item["data"])
            return results
        return {"status": "success"}

    def save_metric(self, portfolio_id: str, metric_data: Any) -> bool:
        _IN_MEMORY_DB.append({
            "table": "metrics",
            "data": {"portfolio_id": portfolio_id, "metric": metric_data}
        })
        return True


db_storage = DBStorage()
