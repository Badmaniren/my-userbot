import json
import os
import sqlite3
import requests
from bs4 import BeautifulSoup


class MarketDatabaseStorage:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

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
                return float(element.text)
            return None
        except Exception:
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
        elif self.storage_file.endswith('.json'):
            records = []
            if os.path.exists(self.storage_file):
                try:
                    with open(self.storage_file, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                        if not isinstance(records, list):
                            records = []
                except Exception:
                    records = []
            records.append({"symbol": symbol, "price": price})
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=4)
        else:
            # Fallback for mock or other file types
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
                    return []
            return []
        else:
            with open(filename, 'rb') as f:
                lines = f.readlines()
                return [line.decode('utf-8') for line in lines]


DbStorage = MarketDatabaseStorage
MarketParser = MarketDatabaseStorage
