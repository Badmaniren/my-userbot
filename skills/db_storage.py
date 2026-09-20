import json
import os
import sqlite3
import requests
from bs4 import BeautifulSoup


class DBStorage:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def save_data(self, filename_or_data, data=None):
        if data is None:
            filename = self.storage_file
            data = filename_or_data
        else:
            filename = filename_or_data

        if filename.endswith('.json'):
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        elif filename.endswith('.db'):
            conn = sqlite3.connect(filename)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    price REAL
                )
            ''')
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        cursor.execute(
                            'INSERT INTO market_data (symbol, price) VALUES (?, ?)',
                            (item.get('symbol', ''), item.get('price', 0.0))
                        )
            conn.commit()
            conn.close()
        else:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(str(data))

    def load_data(self, filename: str = None):
        if filename is None:
            filename = self.storage_file
        return load_data(filename)


DbStorage = DBStorage
MarketStorage = DBStorage
MarketDatabaseStorage = DBStorage


def load_data(filename: str):
    if filename.endswith('.json'):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    elif filename.endswith('.db'):
        if not os.path.exists(filename):
            return []
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT symbol, price FROM market_data')
            rows = cursor.fetchall()
            return [f"{row[0]},{row[1]}\n" for row in rows]
        except (sqlite3.Error, OSError):
            return []
        finally:
            conn.close()
    else:
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                lines = f.readlines()
                return [line.decode('utf-8') for line in lines]
        return []


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
        else:
            with open(filename, 'rb') as f:
                lines = f.readlines()
                return [line.decode('utf-8') for line in lines]
