import sqlite3
import json
import os
import requests
from bs4 import BeautifulSoup


def save_data(filename: str, data):
    """Сохранение данных в файл в формате JSON или DB."""
    if isinstance(filename, str) and filename.endswith('.db'):
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        if isinstance(data, dict):
            for sym, val in data.items():
                cursor.execute('INSERT INTO market_data (symbol, price) VALUES (?, ?)', (sym, float(val)))
        conn.commit()
        conn.close()
    else:
        with open(filename, 'w', encoding='utf-8') as f:
            if isinstance(data, (dict, list)):
                json.dump(data, f)
            else:
                f.write(str(data))


def load_data(filename: str):
    """Загрузка данных из файла."""
    if not os.path.exists(filename):
        return None
    if isinstance(filename, str) and filename.endswith('.db'):
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
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return None
            try:
                return json.loads(content)
            except (json.JSONDecodeError, TypeError):
                return None


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
