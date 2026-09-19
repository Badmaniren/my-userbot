import os
import json
import sqlite3
import requests
from bs4 import BeautifulSoup


class MarketParser:
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
                try:
                    return float(element.text)
                except ValueError:
                    return element.text
            return None
        except Exception:
            return None

    def fetch_and_store(self, symbol: str, price: float):
        if not self.storage_file:
            return True

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
            return True
        elif self.storage_file.endswith('.json'):
            data = {}
            if os.path.exists(self.storage_file):
                try:
                    with open(self.storage_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            if not isinstance(data, dict):
                data = {}
            data[symbol] = {"price": price}
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        else:
            with open(self.storage_file, 'a', encoding='utf-8') as f:
                f.write(f"{symbol},{price}\n")
            return True

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
        else:
            with open(filename, 'rb') as f:
                lines = f.readlines()
                return [line.decode('utf-8') for line in lines]


MarketStorage = MarketParser
MarketDatabaseStorage = MarketParser
DbStorage = MarketParser
DBStorage = MarketParser


_default_db_parser = MarketParser()


def fetch_price(url: str):
    return _default_db_parser.fetch_price(url)


def parse_html_prices(url: str):
    return _default_db_parser.parse_html_prices(url)


def fetch_and_store(symbol: str, price: float):
    return _default_db_parser.fetch_and_store(symbol, price)


def load_data(filename: str):
    return _default_db_parser.load_data(filename)
