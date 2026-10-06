import unittest
import uuid
import io
import random

from skills.market_portfolio_audit_storage_snapshot_index import (
    MarketPortfolioAuditStorageSnapshotIndex,
    SnapshotIndexError,
    IntegrityViolationError,
    market_portfolio_audit_storage_snapshot_index
)
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent


class RealExtractorTool:
    def process(self, stream: io.BytesIO) -> dict:
        data = stream.read().decode('utf-8')
        return {
            "snapshot_id": "processed_" + str(uuid.uuid4()),
            "content_length": len(data),
            "integrity_hash": str(uuid.uuid5(uuid.NAMESPACE_DNS, data))
        }

    def verify(self, stream: io.BytesIO) -> bool:
        content = stream.read()
        return len(content) > 0


class RealAnomalyDetector:
    def analyze(self, data: dict) -> bool:
        return "content_length" in data


class IntegrationTestMarketPortfolioAuditStorageSnapshotIndex(unittest.TestCase):

    def setUp(self):
        self.raw_storage = db_storage()
        self.collector = market_portfolio_collector_agent()
        self.extractor_1 = RealExtractorTool()
        self.extractor_2 = RealExtractorTool()
        self.anomaly_detector = RealAnomalyDetector()

        self.indexer = MarketPortfolioAuditStorageSnapshotIndex(
            db_storage=self.raw_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            market_anomaly_detector=self.anomaly_detector
        )

    def test_factory_function_integration(self):
        default_instance = market_portfolio_audit_storage_snapshot_index()
        self.assertIsInstance(default_instance, MarketPortfolioAuditStorageSnapshotIndex)
        self.assertIsNotNone(default_instance.db_storage)

    def test_index_and_retrieve_snapshot_integration(self):
        random_id = str(uuid.uuid4())
        test_payload = f"portfolio_data_{random.randint(1000, 9999)}".encode('utf-8')
        self.raw_storage.save_snapshot_raw(random_id, io.BytesIO(test_payload))

        result = self.indexer.index_and_retrieve_snapshot(random_id)
        self.assertIsInstance(result, dict)
        self.assertIn("snapshot_id", result)
        self.assertIn("hash", result)

    def test_verify_and_index_integration(self):
        random_id = str(uuid.uuid4())
        test_payload = f"audit_check_{random.randint(1, 100)}".encode('utf-8')
        self.raw_storage.save_snapshot_raw(random_id, io.BytesIO(test_payload))

        is_valid = self.indexer.verify_and_index(random_id)
        self.assertTrue(is_valid)

    def test_batch_index_integration(self):
        id_list = [str(uuid.uuid4()), str(uuid.uuid4())]
        for sid in id_list:
            self.raw_storage.save_snapshot_raw(sid, io.BytesIO(b"batch_test"))

        results = self.indexer.batch_index(id_list)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(id_list))

    def test_index_and_search_integration(self):
        random_id = str(uuid.uuid4())
        self.raw_storage.save_audit_snapshot(random_id, {"status": "indexed_ok"})
        search_result = self.indexer.index_and_search(random_id)

        self.assertIsInstance(search_result, dict)
        self.assertEqual(search_result.get("snapshot_id"), random_id)
        self.assertTrue(search_result.get("indexed"))
        self.assertEqual(search_result.get("status"), "indexed_ok")


if __name__ == "__main__":
    unittest.main()
