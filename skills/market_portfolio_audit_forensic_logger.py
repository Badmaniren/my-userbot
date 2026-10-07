import os
import sqlite3
import hashlib
import json
import io
import requests

class ForensicChainIntegrityError(Exception):
    """Исключение, выбрасываемое при нарушении целостности цепочки форензик-логов."""
    pass


class DatabaseStorage:
    """Хранилище базы данных для интеграционных тестов."""
    def __init__(self, db_path=":memory:"):
        self.db_path = db_path
        if self.db_path == ":memory:":
            self.db_path = f"file:mem_db_{id(self)}?mode=memory&cache=shared"
        self._is_uri = self.db_path.startswith("file:")
        self._keepalive = sqlite3.connect(self.db_path, uri=self._is_uri)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, uri=self._is_uri)

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forensic_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE,
                discrepancy_code TEXT,
                chain_previous_hash TEXT,
                integrity_hash TEXT,
                payload TEXT
            )
        """)
        conn.commit()
        conn.close()

    def get_forensic_record(self, event_id: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT event_id, discrepancy_code, chain_previous_hash, integrity_hash, payload FROM forensic_audit_logs WHERE event_id = ?",
            (event_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "event_id": row[0],
            "discrepancy_code": row[1],
            "chain_previous_hash": row[2],
            "integrity_hash": row[3],
            "payload": json.loads(row[4])
        }


class ForensicLogger:
    """Модуль форензик-логирования с контролем целостности цепочки (юнит-тесты)."""

    def __init__(self, db_storage_path=":memory:", secret_salt=""):
        self.db_storage_path = db_storage_path
        if self.db_storage_path == ":memory:":
            self.db_storage_path = f"file:mem_log_{id(self)}?mode=memory&cache=shared"
        self._is_uri = self.db_storage_path.startswith("file:")
        self.secret_salt = secret_salt
        self._keepalive = sqlite3.connect(self.db_storage_path, uri=self._is_uri)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_storage_path, uri=self._is_uri)

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forensic_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                discrepancy_code TEXT,
                chain_previous_hash TEXT,
                integrity_hash TEXT,
                payload TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log_forensic_event(self, payload: dict):
        self._init_db()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT integrity_hash FROM forensic_audit_logs ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        prev_hash = row[0] if row and row[0] is not None else hashlib.sha256(b"genesis").hexdigest()

        payload_str = json.dumps(payload, sort_keys=True)
        current_hash = hashlib.sha256((prev_hash + payload_str + self.secret_salt).encode()).hexdigest()

        cursor.execute(
            "INSERT INTO forensic_audit_logs (chain_previous_hash, integrity_hash, payload) VALUES (?, ?, ?)",
            (prev_hash, current_hash, payload_str)
        )
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        return log_id

    def verify_chain_integrity(self) -> bool:
        self._init_db()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, event_id, discrepancy_code, chain_previous_hash, integrity_hash, payload FROM forensic_audit_logs ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            _, event_id, discrepancy_code, db_prev_hash, db_curr_hash, payload_str = row
            if event_id is not None or discrepancy_code is not None:
                # Совместимость с форматом ForensicLogAuditor
                ev = event_id if event_id is not None else ""
                disc = discrepancy_code if discrepancy_code is not None else ""
                recalculated_hash = hashlib.sha256((db_prev_hash + ev + disc + payload_str).encode()).hexdigest()
            else:
                recalculated_hash = hashlib.sha256((db_prev_hash + payload_str + self.secret_salt).encode()).hexdigest()
            if recalculated_hash != db_curr_hash:
                raise ForensicChainIntegrityError("Chain integrity violation detected!")
        return True

    def export_audit_trail(self, target_path: str) -> int:
        self._init_db()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, chain_previous_hash, integrity_hash, payload FROM forensic_audit_logs")
        rows = cursor.fetchall()
        conn.close()

        dump_data = []
        for r in rows:
            dump_data.append({"id": r[0], "prev_hash": r[1], "hash": r[2], "payload": r[3]})

        content = json.dumps(dump_data, indent=2)
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return len(content.encode('utf-8'))

    def log_portfolio_discrepancy(self, portfolio_uuid: str, discrepancy_code: str) -> str:
        self._init_db()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT integrity_hash FROM forensic_audit_logs ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        prev_hash = row[0] if row and row[0] is not None else hashlib.sha256(b"genesis").hexdigest()

        payload = {"portfolio_uuid": portfolio_uuid, "discrepancy_code": discrepancy_code}
        payload_str = json.dumps(payload, sort_keys=True)
        current_hash = hashlib.sha256((prev_hash + payload_str + self.secret_salt).encode()).hexdigest()

        cursor.execute(
            "INSERT INTO forensic_audit_logs (chain_previous_hash, integrity_hash, payload) VALUES (?, ?, ?)",
            (prev_hash, current_hash, payload_str)
        )
        conn.commit()
        conn.close()
        return current_hash

    def ingest_external_audit_stream(self, url: str) -> str:
        response = requests.get(url)
        raw_data = response.raw.read() if hasattr(response, 'raw') and response.raw else response.content
        return hashlib.sha256(raw_data).hexdigest()


class ForensicLogAuditor:
    """Аудитор форензик-логов для интеграционных тестов."""

    def __init__(self, db_storage: DatabaseStorage, secret_salt=""):
        self.db_storage = db_storage
        self.secret_salt = secret_salt
        if hasattr(self.db_storage, "_init_db"):
            self.db_storage._init_db()

    def _get_connection(self):
        if hasattr(self.db_storage, "_get_connection"):
            return self.db_storage._get_connection()
        is_uri = getattr(self.db_storage, "_is_uri", getattr(self.db_storage, "db_path", "").startswith("file:"))
        return sqlite3.connect(self.db_storage.db_path, uri=is_uri)

    def log_audit_event(self, event_id: str, discrepancy_code: str, payload: dict):
        if hasattr(self.db_storage, "_init_db"):
            self.db_storage._init_db()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT integrity_hash FROM forensic_audit_logs ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        prev_hash = row[0] if row and row[0] is not None else hashlib.sha256(b"genesis").hexdigest()

        payload_str = json.dumps(payload, sort_keys=True)
        current_hash = hashlib.sha256((prev_hash + event_id + discrepancy_code + payload_str).encode()).hexdigest()

        cursor.execute(
            "INSERT INTO forensic_audit_logs (event_id, discrepancy_code, chain_previous_hash, integrity_hash, payload) VALUES (?, ?, ?, ?, ?)",
            (event_id, discrepancy_code, prev_hash, current_hash, payload_str)
        )
        conn.commit()
        conn.close()

        return {
            "event_id": event_id,
            "discrepancy_code": discrepancy_code,
            "chain_previous_hash": prev_hash,
            "integrity_hash": current_hash,
            "payload": payload
        }

    def verify_chain_integrity(self, secret_salt=None) -> dict:
        if hasattr(self.db_storage, "_init_db"):
            self.db_storage._init_db()
        salt = secret_salt if secret_salt is not None else self.secret_salt
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT event_id, discrepancy_code, chain_previous_hash, integrity_hash, payload FROM forensic_audit_logs ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()

        hashes = []
        for row in rows:
            event_id, discrepancy_code, db_prev_hash, db_curr_hash, payload_str = row
            if event_id is None and discrepancy_code is None:
                recalculated = hashlib.sha256((db_prev_hash + payload_str + salt).encode()).hexdigest()
            else:
                ev = event_id if event_id is not None else ""
                disc = discrepancy_code if discrepancy_code is not None else ""
                recalculated = hashlib.sha256((db_prev_hash + ev + disc + payload_str).encode()).hexdigest()

            if recalculated != db_curr_hash:
                raise ForensicChainIntegrityError("Integration chain integrity validation failed!")
            hashes.append(db_curr_hash)

        return {
            "is_valid": True,
            "checked_nodes_count": len(hashes),
            "hashes": hashes
        }
