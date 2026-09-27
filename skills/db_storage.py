import json
import os
import sqlite3
import requests
from bs4 import BeautifulSoup


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("price")

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
            finally:
                conn.close()
            return data
        else:
            with open(filename, 'rb') as f:
                lines = f.readlines()
                return [line.decode('utf-8') for line in lines]


def save_portfolio(data, filepath):
    if not filepath:
        return False
    dirname = os.path.dirname(filepath)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    if str(filepath).endswith('.db'):
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL
            )
        ''')
        cursor.execute('INSERT INTO portfolio (data) VALUES (?)', (json.dumps(data),))
        conn.commit()
        conn.close()
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    return True


def load_portfolio(filepath):
    if not filepath or not os.path.exists(filepath):
        return {}
    if str(filepath).endswith('.db'):
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        try:
            cursor.execute('CREATE TABLE IF NOT EXISTS portfolio (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)')
            cursor.execute('SELECT data FROM portfolio ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
        except sqlite3.Error:
            pass
        finally:
            conn.close()
        return {}
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)