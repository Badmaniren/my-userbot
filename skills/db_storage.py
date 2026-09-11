import sqlite3
import json
import time

class DBStorage:
    def __init__(self, db_path="storage.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS data (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    expires_at REAL
                )
            """)

    def save_data(self, key, value):
        serialized = json.dumps(value)
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO data (key, value) VALUES (?, ?)",
                (key, serialized)
            )

    def get_data(self, key):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM data WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def set_cache(self, key, value, ttl=0):
        current_time = time.time()
        expires_at = current_time + ttl if ttl > 0 else 0
        serialized = json.dumps(value)
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, serialized, expires_at)
            )

    def get_cache(self, key):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value, expires_at FROM cache WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row is None:
            return None
        
        value, expires_at = row
        current_time = time.time()
        
        if expires_at > 0 and current_time >= expires_at:
            with self.conn:
                self.conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            return None
            
        return json.loads(value)