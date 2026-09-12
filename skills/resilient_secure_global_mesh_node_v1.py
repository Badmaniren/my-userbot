import sqlite3
import json
import requests
import io

class ResilientSecureSmartCrawlerHubV11GlobalMeshError(Exception):
    """Кастомное исключение для ошибок глобальной меш-сети узла."""
    pass

class ResilientSecureSmartCrawlerHubV11GlobalMesh:
    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=1.0, raise_on_limit=True):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit
        
        self._init_db()

    def _init_db(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                target TEXT PRIMARY KEY,
                data TEXT
            )
        """)
        self.conn.commit()

    def validate_target_headers(self, url: str, timeout: int) -> bool:
        try:
            response = requests.head(url, timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False

    def coordinate_expansion(self, url: str, timeout: int) -> bool:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return True
            raise ResilientSecureSmartCrawlerHubV11GlobalMeshError("Expansion failed with status code != 200")
        except Exception as e:
            if isinstance(e, ResilientSecureSmartCrawlerHubV11GlobalMeshError):
                raise
            raise ResilientSecureSmartCrawlerHubV11GlobalMeshError(f"Expansion failed: {e}")

    def coordinate_expansion_safe(self, url: str, timeout: int) -> bool:
        try:
            return self.coordinate_expansion(url, timeout)
        except Exception:
            return False

    def export_analytics_report(self, target: str, report_data: dict) -> None:
        data_str = json.dumps(report_data)
        self.cursor.execute(
            "INSERT OR REPLACE INTO reports (target, data) VALUES (?, ?)",
            (target, data_str)
        )
        self.conn.commit()

    def get_exported_report(self, target: str) -> dict:
        self.cursor.execute("SELECT data FROM reports WHERE target = ?", (target,))
        row = self.cursor.fetchone()
        if row:
            return json.loads(row[0])
        return {}

    def process_stream(self, url: str, timeout: int) -> None:
        try:
            response = requests.get(url, stream=True, timeout=timeout)
            if response.status_code == 200:
                raw_obj = response.raw
                if hasattr(raw_obj, "stream"):
                    for _ in raw_obj.stream(1024):
                        pass
                else:
                    for _ in iter(lambda: raw_obj.read(1024), b""):
                        pass
            else:
                raise ResilientSecureSmartCrawlerHubV11GlobalMeshError("Stream error: status code != 200")
        except Exception as e:
            if isinstance(e, ResilientSecureSmartCrawlerHubV11GlobalMeshError):
                raise
            raise ResilientSecureSmartCrawlerHubV11GlobalMeshError(f"Stream down: {e}")