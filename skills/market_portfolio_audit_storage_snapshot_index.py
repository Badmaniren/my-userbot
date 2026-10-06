import io
import uuid
import os

try:
    from skills.db_storage import db_storage
except ImportError:
    db_storage = None

try:
    from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
except ImportError:
    market_portfolio_collector_agent = None


class SnapshotIndexError(Exception):
    """Исключение при ошибке индексации снапшота."""
    pass


class IntegrityViolationError(SnapshotIndexError):
    """Исключение при нарушении целостности снапшота."""
    pass


class MarketPortfolioAuditStorageSnapshotIndex:
    def __init__(self, db_storage=None, extractor_tool_1790087207=None, extractor_tool_1790102839=None, market_anomaly_detector=None):
        self.db_storage = db_storage
        self.extractor_tool_1 = extractor_tool_1790087207
        self.extractor_tool_2 = extractor_tool_1790102839
        self.market_anomaly_detector = market_anomaly_detector

    def index_and_retrieve_snapshot(self, snapshot_id: str) -> dict:
        if self.db_storage is None or not hasattr(self.db_storage, "fetch_snapshot_raw"):
            raise SnapshotIndexError("db_storage is not configured or lacks fetch_snapshot_raw")

        stream = self.db_storage.fetch_snapshot_raw(snapshot_id)
        if stream is None:
            raise SnapshotIndexError("Storage stream is empty")

        content = stream.read()
        if len(content) == 0:
            raise SnapshotIndexError("Storage stream is empty")

        stream.seek(0)

        if self.extractor_tool_1:
            extracted_data = self.extractor_tool_1.process(stream)
        else:
            extracted_data = {"snapshot_id": snapshot_id}

        if not isinstance(extracted_data, dict):
            extracted_data = {"snapshot_id": snapshot_id}

        if "snapshot_id" not in extracted_data:
            extracted_data["snapshot_id"] = snapshot_id
        if "hash" not in extracted_data and "integrity_hash" in extracted_data:
            extracted_data["hash"] = extracted_data["integrity_hash"]

        if self.market_anomaly_detector:
            is_normal = self.market_anomaly_detector.analyze(extracted_data)
            if not is_normal:
                raise SnapshotIndexError("Market anomaly detected")

        return extracted_data

    def verify_and_index(self, snapshot_id: str) -> bool:
        if self.db_storage is None or not hasattr(self.db_storage, "fetch_snapshot_raw"):
            raise SnapshotIndexError("db_storage is not configured or lacks fetch_snapshot_raw")

        stream = self.db_storage.fetch_snapshot_raw(snapshot_id)
        if stream is None:
            raise IntegrityViolationError("Storage stream is empty")

        if self.extractor_tool_2:
            is_valid = self.extractor_tool_2.verify(stream)
            if not is_valid:
                raise IntegrityViolationError("Integrity check failed")

        return True

    def batch_index(self, snapshot_ids: list) -> list:
        if self.db_storage is None or not hasattr(self.db_storage, "fetch_snapshot_raw"):
            raise SnapshotIndexError("db_storage is not configured or lacks fetch_snapshot_raw")

        results = []
        for sid in snapshot_ids:
            stream = self.db_storage.fetch_snapshot_raw(sid)
            if self.extractor_tool_1 and stream is not None:
                res = self.extractor_tool_1.process(stream)
                results.append(res)
            else:
                results.append({"snapshot_id": sid})
        return results

    def index_and_search(self, snapshot_id: str) -> dict:
        if self.db_storage and hasattr(self.db_storage, "get_audit_snapshot"):
            record = self.db_storage.get_audit_snapshot(snapshot_id)
        else:
            record = {}

        result = {
            "snapshot_id": snapshot_id,
            "indexed": True,
            "index_file_path": ""
        }
        if record:
            result.update(record)
        return result


def market_portfolio_audit_storage_snapshot_index():
    if db_storage is not None:
        return MarketPortfolioAuditStorageSnapshotIndex(db_storage=db_storage())
    return MarketPortfolioAuditStorageSnapshotIndex(db_storage=None)
