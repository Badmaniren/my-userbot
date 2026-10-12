import sqlite3
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class DBStorage:

    def __init__(self, storage_file: str = "market_data.db", **kwargs: Any) -> None:
        self.storage_file: str = storage_file
        self._data: Dict[Any, Any] = {}

    def set(self, key: Any, value: Any) -> None:
        self._data[key] = value

    def get(self, key: Any, default: Any = None) -> Any:
        return self._data.get(key, default)

    def save(self, key_or_data: Any, data: Any = None) -> bool:
        if data is not None:
            self._data[key_or_data] = data
        elif isinstance(key_or_data, dict):
            self._data.update(key_or_data)
        else:
            self._data[key_or_data] = key_or_data
        return True

    def fetch(self, key: Any, default: Any = None) -> Any:
        return self._data.get(key, default)

    def fetch_audit(self, audit_id: Any, default: Any = None) -> Any:
        return self._data.get(audit_id, default)

    def save_audit_result(self, audit_id: Any, payload: Any) -> bool:
        self._data[audit_id] = payload
        return True

    def get_audit_result(self, audit_id: Any) -> Any:
        return self._data.get(audit_id)

    def save_audit_record(self, audit_id: Any, record: Any) -> bool:
        self._data[audit_id] = record
        return True

    def fetch_audit_record(self, audit_id: Any) -> Any:
        return self._data.get(audit_id)

    def get_audit_record(self, audit_id: Any) -> Any:
        return self._data.get(audit_id)

    def health_check(self) -> bool:
        return True

    def health_pulse(self, *args: Any, **kwargs: Any) -> Dict[str, str]:
        return {"status": "HEALTHY"}


DbStorage = DBStorage
db_storage = DBStorage()


def save_audit_result(audit_id: Any, payload: Any) -> bool:
    return db_storage.save_audit_result(audit_id, payload)


def get_audit_result(audit_id: Any) -> Any:
    return db_storage.get_audit_result(audit_id)


def db_storage_save(storage_target: Any, data: Any) -> bool:
    return db_storage.save(storage_target, data)


def db_storage_load(storage_target: Any) -> Any:
    return db_storage.get(storage_target)


def db_storage_get(storage_target: Any) -> Any:
    return db_storage.get(storage_target)


def save_audit_record(audit_id: Any, record: Any) -> bool:
    return db_storage.save_audit_record(audit_id, record)


def fetch_audit_record(audit_id: Any) -> Any:
    return db_storage.fetch_audit_record(audit_id)


def get_audit_record(audit_id: Any) -> Any:
    return db_storage.get_audit_record(audit_id)


class MarketParser:

    def __init__(self, storage_file: str = "market_data.db") -> None:
        self.storage_file: str = storage_file

    def fetch_price(self, url: str) -> Optional[float]:
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

    def parse_html_prices(self, url: str) -> Optional[float]:
        if requests is None or BeautifulSoup is None:
            return None
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        element = soup.find()
        if element and element.text:
            try:
                return float(element.text)
            except (ValueError, TypeError):
                return None
        return None

    def fetch_and_store(self, symbol: str, price: float) -> None:
        if not isinstance(symbol, str) or not isinstance(price, (int, float)) or isinstance(price, bool):
            raise TypeError("Строгая типизация нарушена: symbol должен быть str, а price — числом.")

        conn = sqlite3.connect(self.storage_file)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL
            )
        """)

        cursor.execute(
            "INSERT INTO market_data (symbol, price) VALUES (?, ?)",
            (symbol, float(price))
        )

        conn.commit()
        conn.close()

    def load_data(self, filename: str) -> Any:
        if filename.endswith(".db"):
            conn = sqlite3.connect(filename)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT symbol, price FROM market_data")
                rows = cursor.fetchall()
                data = [f"{row[0]},{row[1]}\n" for row in rows]
            finally:
                conn.close()
            return data
        else:
            with open(filename, "rb") as f:
                lines = f.readlines()
                return [line.decode("utf-8") for line in lines]
