import unittest
import tempfile
import os
import uuid
import random
from skills.market_anomaly_detector import MarketAnomalyDetector

class TestMarketAnomalyDetectorIntegration(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)

        self.storage_fd, self.storage_file = tempfile.mkstemp(suffix=".json")
        os.close(self.storage_fd)

        self.detector = MarketAnomalyDetector(db_path=self.db_path)

        self.symbol = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/api/v1/report/{uuid.uuid4().hex}"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:10]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.min_threshold = round(random.uniform(0.01, 0.99), 2)
        self.channels = ["telegram", "webhook"]

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_detect_and_dispatch_integration_flow(self):
        random_anomaly_marker = uuid.uuid4().hex
        raw_payload = f"INSIDER_TRADE_VOLUME_SPIKE: {random_anomaly_marker} VALUE: {random.randint(10000, 999999)}".encode('utf-8')

        result = self.detector.detect_and_dispatch(
            ticker=self.symbol,
            raw_data_stream=raw_payload,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertIn("anomaly_detected", result)
        self.assertIn("activity_details", result)
        self.assertIsInstance(result["anomaly_detected"], bool)
        self.assertIsInstance(result["activity_details"], dict)

        stream_bytes_result = self.detector.process_raw_stream_bytes(raw_payload)
        self.assertIsInstance(stream_bytes_result, dict)

        legacy_detect_result = self.detector.detect_anomaly(
            raw_data_stream=raw_payload,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )
        self.assertIsInstance(legacy_detect_result, dict)

if __name__ == "__main__":
    unittest.main()