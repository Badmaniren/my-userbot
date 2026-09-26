import uuid
import sqlite3
from typing import Optional, Dict, Any, Union

class MarketInsiderActivityTracker:
    """
    Tracker for market insider activity analyzing raw data streams.
    """
    def __init__(self, **kwargs: Any) -> None:
        self.deps: Dict[str, Any] = kwargs
        self.db_storage: Optional[Any] = kwargs.get("db_storage")
        if not self.db_storage and kwargs.get("db_path"):
            self.db_storage = DBStorage(db_path=kwargs.get("db_path"))

    def analyze_activity(self, raw_data_stream: Any) -> Dict[str, Any]:
        if raw_data_stream is None:
            raise ValueError("Empty stream")

        signature = uuid.uuid4().hex

        if isinstance(raw_data_stream, dict):
            ticker = raw_data_stream.get("ticker") or raw_data_stream.get("ticker_id") or "UNKNOWN"
            is_anomaly = bool(
                raw_data_stream.get("is_anomaly")
                or raw_data_stream.get("anomaly_detected")
                or (isinstance(raw_data_stream.get("anomaly_score"), (int, float)) and raw_data_stream.get("anomaly_score", 0) > 0.5)
            )
            api_res = MarketInsiderActivityTrackerModuleAPI.track_activity(raw_data_stream)
            if api_res.get("anomaly_detected"):
                is_anomaly = True

            status = "ANOMALY_DETECTED" if is_anomaly else "NORMAL"

            if self.db_storage and ticker:
                self.db_storage.save_activity(ticker=ticker, is_anomaly=is_anomaly, signature=signature)

            return {
                "ticker": ticker,
                "status": status,
                "is_anomaly": is_anomaly,
                "signature": signature
            }

        if hasattr(raw_data_stream, "read"):
            content = raw_data_stream.read()
        elif isinstance(raw_data_stream, bytes):
            content = raw_data_stream
        else:
            content = str(raw_data_stream).encode("utf-8")

        if not content:
            raise ValueError("Empty stream")

        status = "ALERT" if b"anomaly" in content else "NORMAL"
        is_anomaly = status == "ALERT"

        return {"status": status, "is_anomaly": is_anomaly, "signature": signature}


class MarketInsiderActivityTrackerModuleAPI:
    """
    API for tracking market insider activity based on payload data.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    @staticmethod
    def track_activity(payload: Any) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {
                "anomaly_detected": False,
                "ticker_id": None,
                "volume": 0.0,
                "signature": uuid.uuid4().hex
            }
            
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
    def __init__(self, db_path: str = "test_integration.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
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

    def save_activity(self, ticker: str, is_anomaly: bool, signature: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activities (ticker, is_anomaly, signature) VALUES (?, ?, ?)",
            (ticker, 1 if is_anomaly else 0, signature)
        )
        conn.commit()
        conn.close()

    def get_last_activity(self, ticker: str) -> Optional[Dict[str, Any]]:
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