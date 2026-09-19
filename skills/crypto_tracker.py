import sqlite3
import datetime
import requests

class CryptoTracker:
    def __init__(self, db_path="crypto.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                btc_price REAL,
                eth_price REAL,
                percentage_diff REAL,
                timestamp TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                btc_price REAL,
                eth_price REAL,
                percentage_diff REAL,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    def fetch_prices(self):
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum",
            "vs_currencies": "usd"
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                btc = data.get("bitcoin", {}).get("usd")
                eth = data.get("ethereum", {}).get("usd")
                if btc is not None and eth is not None:
                    return {"btc": float(btc), "eth": float(eth)}
            return None
        except requests.exceptions.RequestException:
            return None

    def calculate_percentage_difference(self, btc_price, eth_price):
        if eth_price == 0.0 or eth_price == 0:
            return 0.0
        return ((btc_price - eth_price) / eth_price) * 100.0

    def save_record(self, btc_price, eth_price, percentage_diff):
        timestamp = datetime.datetime.utcnow().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for table in ["crypto_records", "crypto_prices"]:
            cursor.execute(f"""
                INSERT INTO {table} (btc_price, eth_price, percentage_diff, timestamp)
                VALUES (?, ?, ?, ?)
            """, (btc_price, eth_price, percentage_diff, timestamp))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def track_and_save(self):
        prices = self.fetch_prices()
        if not prices:
            return False
        btc = prices.get("btc")
        eth = prices.get("eth")
        diff = self.calculate_percentage_difference(btc, eth)
        self.save_record(btc, eth, diff)
        return True

    def fetch_and_save_prices(self):
        prices = self.fetch_prices()
        if not prices:
            return None
        btc = prices.get("btc")
        eth = prices.get("eth")
        diff = self.calculate_percentage_difference(btc, eth)
        timestamp = datetime.datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO crypto_prices (btc_price, eth_price, percentage_diff, timestamp)
            VALUES (?, ?, ?, ?)
        """, (btc, eth, diff, timestamp))
        conn.commit()
        record_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO crypto_records (btc_price, eth_price, percentage_diff, timestamp)
            VALUES (?, ?, ?, ?)
        """, (btc, eth, diff, timestamp))
        conn.commit()
        conn.close()
        return record_id