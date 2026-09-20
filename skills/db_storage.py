import json
import os
import sqlite3
import uuid
import requests
from bs4 import BeautifulSoup


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            return data.get("price")
        except Exception:
            return None

    def parse_html_prices(self, url: str):
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find()
        if element and element.text:
            return float(element.text)
        return None

    def fetch_and_store(self, symbol: str, price: float):
        if not self.storage_file:
            return None
        if self.storage_file.endswith('.json'):
            data = {}
            if os.path.exists(self.storage_file):
                try:
                    with open(self.storage_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            record_id = str(uuid.uuid4())
            data[symbol] = {
                "price": price,
                "record_id": record_id
            }
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return record_id
        else:
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
                    return {}
            return {}
        else:
            with open(filename, 'rb') as f:
                lines = f.readlines()
                return [line.decode('utf-8') for line in lines]


def load_data(filename: str):
    return MarketParser().load_data(filename)


MarketStorage = MarketParser
MarketDatabaseStorage = MarketParser
DbStorage = MarketParser
DBStorage = MarketParser
