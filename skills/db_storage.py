import sqlite3
from typing import Optional, Dict, Any

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
        data = response.json()
        return data.get("price")

    def parse_html_prices(self, url: str):
        if requests is None or BeautifulSoup is None:
            return None
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


class DBStorage:
    """
    Database storage implementation for macro liquidity tracking and market activity logs.
    """
    def __init__(self, db_path: str = "test_macro_liquidity.db", **kwargs: Any) -> None:
        self.db_path = db_path
        self._memory_data: Dict[str, Dict[str, Any]] = {}
        self._init_db()

    def _init_db(self) -> None:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS macro_liquidity (
                    tracking_id TEXT PRIMARY KEY,
                    interest_rate REAL,
                    market_volume INTEGER
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT,
                    is_anomaly INTEGER,
                    signature TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception:
            pass

    def save_macro_liquidity(self, data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            return
        tracking_id = str(data.get("tracking_id", ""))
        interest_rate = data.get("interest_rate", 0.0)
        market_volume = data.get("market_volume", 0)
        self._memory_data[tracking_id] = data
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO macro_liquidity (tracking_id, interest_rate, market_volume) VALUES (?, ?, ?)",
                (tracking_id, interest_rate, market_volume)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def save(self, data: Dict[str, Any]) -> None:
        if isinstance(data, dict) and "tracking_id" in data:
            self.save_macro_liquidity(data)
        elif isinstance(data, dict):
            t_id = str(data.get("id") or data.get("tracking_id") or "default")
            self._memory_data[t_id] = data

    def get_macro_liquidity(self, tracking_id: str) -> Optional[Dict[str, Any]]:
        if tracking_id in self._memory_data:
            return self._memory_data[tracking_id]
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT tracking_id, interest_rate, market_volume FROM macro_liquidity WHERE tracking_id = ?",
                (tracking_id,)
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    "tracking_id": row[0],
                    "interest_rate": row[1],
                    "market_volume": row[2]
                }
        except Exception:
            pass
        return None

    def save_activity(self, ticker: str, is_anomaly: bool, signature: str) -> None:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO activities (ticker, is_anomaly, signature) VALUES (?, ?, ?)",
                (ticker, 1 if is_anomaly else 0, signature)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_last_activity(self, ticker: str) -> Optional[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ticker, is_anomaly, signature FROM activities WHERE ticker = ? ORDER BY id DESC LIMIT 1",
                (ticker,)
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    "ticker": row[0],
                    "is_anomaly": bool(row[1]),
                    "signature": row[2]
                }
        except Exception:
            pass
        return None


DbStorage = DBStorage
