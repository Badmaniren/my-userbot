import sqlite3
import json

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
        self.portfolios = {}

    def get_portfolio(self, portfolio_id):
        portfolios = getattr(self, "portfolios", {})
        if isinstance(portfolios, dict):
            return portfolios.get(portfolio_id)
        return None

    def fetch_price(self, url: str):
        if not requests:
            return None
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if isinstance(data, dict):
                return data.get("price")
        except Exception:
            return None
        return None

    def parse_html_prices(self, url: str):
        if not requests or not BeautifulSoup:
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

    def parse_stream(self, stream):
        if isinstance(stream, dict):
            return stream
        if hasattr(stream, "read"):
            try:
                content = stream.read()
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                return json.loads(content)
            except Exception:
                return {}
        if isinstance(stream, (str, bytes)):
            try:
                if isinstance(stream, bytes):
                    stream = stream.decode("utf-8")
                return json.loads(stream)
            except Exception:
                return {}
        return {}


DbStorage = MarketParser
db_storage = MarketParser()
