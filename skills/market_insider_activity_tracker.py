import uuid
import sqlite3
import os

class MarketInsiderActivityTracker:
    """
    Tracker for market insider activity analyzing raw data streams.
    """
    def __init__(self, **kwargs):
        self.deps = kwargs
        self.db_storage = kwargs.get("db_storage")

    def analyze_activity(self, raw_data_stream):
        if raw_data_stream is None:
            raise ValueError("Empty stream")
        
        content = raw_data_stream.read()
        if not content:
            raise ValueError("Empty stream")
        
        signature = uuid.uuid4().hex
        if b"anomaly" in content:
            return {"status": "ALERT", "signature": signature}
        return {"status": "NORMAL", "signature": signature}


class MarketInsiderActivityTrackerModuleAPI:
    """
    API for tracking market insider activity based on payload data.
    """
    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def track_activity(payload):
        if not isinstance(payload, dict):
            payload = {}
            
        ticker_id = payload.get("ticker_id")
        raw_volume = payload.get("volume", 0)
        raw_multiplier = payload.get("anomaly_multiplier", 1.0)
        
        try:
            volume = float(raw_volume)
        except (TypeError, ValueError):
            volume = 0.0

        try:
            multiplier = float(raw_multiplier)
        except (TypeError, ValueError):
            multiplier = 1.0
        
        is_anomaly = volume > 500000.0 or multiplier > 5.0
        
        return {
            "anomaly_detected": is_anomaly,
            "ticker_id": ticker_id,
            "volume": volume,
            "signature": uuid.uuid4().hex
        }


class DBStorage:
    """
    Database storage implementation for market insider activity tracking.
    """
    def __init__(self, db_path="test_integration.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                is_anomaly INTEGER,
                signature TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_activity(self, ticker, is_anomaly, signature):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activities (ticker, is_anomaly, signature) VALUES (?, ?, ?)",
            (ticker, 1 if is_anomaly else 0, signature)
        )
        conn.commit()
        conn.close()

    def get_last_activity(self, ticker):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ticker, is_anomaly, signature FROM activities WHERE ticker = ? ORDER BY id DESC LIMIT 1",
            (ticker,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "ticker": row[0],
                "is_anomaly": bool(row[1]),
                "signature": row[2]
            }
        return None


MarketInsiderActivityTrackerModuleIdempotentProxy = MarketInsiderActivityTrackerModuleAPI

globals()["market_insider_activity_tracker"] = MarketInsiderActivityTrackerModuleAPI
globals()["DBStorage"] = DBStorage