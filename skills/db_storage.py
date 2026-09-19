import os
import json
import sqlite3
import requests
from bs4 import BeautifulSoup


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file
        self._thresholds = {}

    def fetch_price(self, url: str):
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if isinstance(data, dict):
                return data.get("price")
            return data
        except Exception:
            return None

    def parse_html_prices(self, url: str):
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            element = soup.find()
            if element and element.text:
                try:
                    return float(element.text)
                except ValueError:
                    return element.text
            return None
        except Exception:
            return None

    def get_threshold(self, symbol: str):
        return self._thresholds.get(symbol, None)

    def set_threshold(self, symbol: str, threshold: float):
        self._thresholds[symbol] = threshold

    def fetch_and_store(self, symbol, price=None):
        if isinstance(symbol, list):
            for item in symbol:
                if isinstance(item, dict):
                    self.fetch_and_store(item.get("symbol", "UNKNOWN"), item.get("price", 0.0))
            return
        if isinstance(symbol, dict):
            return self.fetch_and_store(symbol.get("symbol", "UNKNOWN"), symbol.get("price", 0.0))

        if not self.storage_file:
            return

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
                (symbol, float(price) if price is not None else 0.0)
            )

            conn.commit()
            conn.close()
        else:
            data = {}
            if os.path.exists(self.storage_file):
                try:
                    with open(self.storage_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            if isinstance(data, dict):
                data[symbol] = {"price": price}
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            else:
                with open(self.storage_file, 'a', encoding='utf-8') as f:
                    f.write(f"{symbol},{price}\n")

    def save_alert(self, alert_data):
        if isinstance(alert_data, dict):
            symbol = alert_data.get("symbol", "UNKNOWN")
            price = alert_data.get("price", 0.0)
        else:
            symbol, price = "UNKNOWN", 0.0
        self.fetch_and_store(symbol, price)

    def store_alert(self, alert_data):
        self.save_alert(alert_data)

    def save(self, alert_data):
        self.save_alert(alert_data)

    def load_data(self, filename: str):
        if filename.endswith('.db'):
            conn = sqlite3.connect(filename)
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT symbol, price FROM market_data')
                rows = cursor.fetchall()
                data = [f"{row[0]},{row[1]}\n" for row in rows]
            except Exception:
                data = []
            finally:
                conn.close()
            return data
        elif filename.endswith('.json'):
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    pass
            return {}
        try:
            with open(filename, 'rb') as f:
                lines = f.readlines()
                return [line.decode('utf-8') for line in lines]
        except Exception:
            return []


DBStorage = MarketParser
