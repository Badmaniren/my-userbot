import unittest
import io
import uuid
import random
from unittest.mock import MagicMock, patch

from skills.market_portfolio_audit_storage_snapshot_index import (
    MarketPortfolioAuditStorageSnapshotIndex,
    SnapshotIndexError,
    IntegrityViolationError,
    market_portfolio_audit_storage_snapshot_index
)


class TestMarketPortfolioAuditStorageSnapshotIndex(unittest.TestCase):

    def setUp(self):
        self.snapshot_id = uuid.uuid4().hex
        self.mock_db = MagicMock()
        self.mock_extractor_1 = MagicMock()
        self.mock_extractor_2 = MagicMock()
        self.mock_anomaly_detector = MagicMock()

    def test_index_and_retrieve_snapshot_success(self):
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        self.mock_db.fetch_snapshot_raw.return_value = stream

        expected_dict = {"snapshot_id": self.snapshot_id, "integrity_hash": uuid.uuid4().hex}
        self.mock_extractor_1.process.return_value = expected_dict
        self.mock_anomaly_detector.analyze.return_value = True

        indexer = MarketPortfolioAuditStorageSnapshotIndex(
            db_storage=self.mock_db,
            extractor_tool_1790087207=self.mock_extractor_1,
            market_anomaly_detector=self.mock_anomaly_detector
        )

        result = indexer.index_and_retrieve_snapshot(self.snapshot_id)

        self.mock_db.fetch_snapshot_raw.assert_called_once_with(self.snapshot_id)
        self.mock_extractor_1.process.assert_called_once()
        self.mock_anomaly_detector.analyze.assert_called_once()
        self.assertEqual(result["snapshot_id"], self.snapshot_id)
        self.assertEqual(result["hash"], expected_dict["integrity_hash"])

    def test_index_and_retrieve_snapshot_empty_stream(self):
        stream = io.BytesIO(b"")
        self.mock_db.fetch_snapshot_raw.return_value = stream

        indexer = MarketPortfolioAuditStorageSnapshotIndex(
            db_storage=self.mock_db
        )

        with self.assertRaises(SnapshotIndexError) as ctx:
            indexer.index_and_retrieve_snapshot(self.snapshot_id)

        self.assertIn("Storage stream is empty", str(ctx.exception))

    def test_index_and_retrieve_snapshot_anomaly_detected(self):
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        self.mock_db.fetch_snapshot_raw.return_value = stream

        self.mock_extractor_1.process.return_value = {"snapshot_id": self.snapshot_id}
        self.mock_anomaly_detector.analyze.return_value = False

        indexer = MarketPortfolioAuditStorageSnapshotIndex(
            db_storage=self.mock_db,
            extractor_tool_1790087207=self.mock_extractor_1,
            market_anomaly_detector=self.mock_anomaly_detector
        )

        with self.assertRaises(SnapshotIndexError) as ctx:
            indexer.index_and_retrieve_snapshot(self.snapshot_id)

        self.assertIn("Market anomaly detected", str(ctx.exception))

    def test_verify_and_index_success(self):
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        self.mock_db.fetch_snapshot_raw.return_value = stream
        self.mock_extractor_2.verify.return_value = True

        indexer = MarketPortfolioAuditStorageSnapshotIndex(
            db_storage=self.mock_db,
            extractor_tool_1790102839=self.mock_extractor_2
        )

        res = indexer.verify_and_index(self.snapshot_id)
        self.assertTrue(res)
        self.mock_extractor_2.verify.assert_called_once_with(stream)

    def test_verify_and_index_integrity_failure(self):
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        self.mock_db.fetch_snapshot_raw.return_value = stream
        self.mock_extractor_2.verify.return_value = False

        indexer = MarketPortfolioAuditStorageSnapshotIndex(
            db_storage=self.mock_db,
            extractor_tool_1790102839=self.mock_extractor_2
        )

        with self.assertRaises(IntegrityViolationError) as ctx:
            indexer.verify_and_index(self.snapshot_id)

        self.assertIn("Integrity check failed", str(ctx.exception))

    def test_batch_index(self):
        ids = [uuid.uuid4().hex for _ in range(3)]
        streams = [io.BytesIO(uuid.uuid4().bytes) for _ in ids]
        self.mock_db.fetch_snapshot_raw.side_effect = streams

        processed_results = [{"snapshot_id": i, "status": uuid.uuid4().hex} for i in ids]
        self.mock_extractor_1.process.side_effect = processed_results

        indexer = MarketPortfolioAuditStorageSnapshotIndex(
            db_storage=self.mock_db,
            extractor_tool_1790087207=self.mock_extractor_1
        )

        results = indexer.batch_index(ids)
        self.assertEqual(len(results), 3)
        for idx, res in enumerate(results):
            self.assertEqual(res["snapshot_id"], ids[idx])

    def test_index_and_search_with_record(self):
        record_key = uuid.uuid4().hex
        record_val = uuid.uuid4().hex
        self.mock_db.get_audit_snapshot.return_value = {record_key: record_val}

        indexer = MarketPortfolioAuditStorageSnapshotIndex(
            db_storage=self.mock_db
        )

        result = indexer.index_and_search(self.snapshot_id)
        self.assertTrue(result["indexed"])
        self.assertEqual(result["snapshot_id"], self.snapshot_id)
        self.assertEqual(result[record_key], record_val)

    def test_factory_function(self):
        with patch("skills.market_portfolio_audit_storage_snapshot_index.db_storage") as mock_db_class:
            mock_instance = MagicMock()
            mock_db_class.return_value = mock_instance

            instance = market_portfolio_audit_storage_snapshot_index()
            self.assertIsInstance(instance, MarketPortfolioAuditStorageSnapshotIndex)
            self.assertEqual(instance.db_storage, mock_instance)