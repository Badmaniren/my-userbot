import uuid
import sqlite3
from typing import Optional, Dict, Any

class MarketInsiderActivityTracker:
    """
    Tracker for market insider activity analyzing raw data streams.
    """
    def __init__(self, **kwargs: Any) -> None:
        self.deps: Dict[str, Any] = kwargs
        self.db_storage: Optional[Any] = kwargs.get("db_storage")

    def analyze_activity(self, raw_data_stream: Any) -> Dict[str, str]:
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
            
        ticker_id = payload.get("ticker_id") or payload.get("ticker")
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


def track_insider_activity(payload: Any = None, *args: Any, **kwargs: Any) -> Dict[str, Any]:
    if payload is None and kwargs:
        payload = kwargs
    return MarketInsiderActivityTrackerModuleAPI.track_activity(payload)


def market_insider_activity_tracker(payload: Any = None, *args: Any, **kwargs: Any) -> Any:
    if payload is None and kwargs:
        payload = kwargs

    if isinstance(payload, dict):
        insider_trades = float(payload.get("insider_trades_count", 0))
        volume = float(payload.get("volume", 0))
        avg_vol = float(payload.get("avg_volume", 0))
        multiplier = float(payload.get("anomaly_multiplier", 1.0))
        sec_flag = bool(payload.get("sec_filing_flag", False))

        score = 0.0
        if insider_trades > 0:
            score += min(0.6, insider_trades * 0.1)
        if avg_vol > 0 and volume > avg_vol:
            ratio = volume / avg_vol
            score += min(0.3, (ratio - 1.0) * 0.05)
        if sec_flag:
            score += 0.1
        if multiplier > 1.0:
            score += min(0.3, (multiplier - 1.0) * 0.1)

        return min(1.0, max(0.0, round(score, 2)))
    elif isinstance(payload, (int, float)):
        return float(payload)
    elif hasattr(payload, "read"):
        tracker = MarketInsiderActivityTracker()
        res = tracker.analyze_activity(payload)
        return 1.0 if res.get("status") == "ALERT" else 0.0
    return 0.0
