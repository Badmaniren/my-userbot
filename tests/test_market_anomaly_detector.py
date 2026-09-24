import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import io
import json

from skills.market_anomaly_detector import MarketAnomalyDetector, market_anomaly_detector


class TestMarketAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_anomaly_storage_{uuid.uuid4().hex[:8]}.json"
        self.detector = MarketAnomalyDetector(storage_file=self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_init(self):
        detector = MarketAnomalyDetector()
        self.assertIsNotNone(detector.db_storage)
        self.assertIsNotNone(market_anomaly_detector)

    def test_analyze_market_data_empty(self):
        res = self.detector.analyze_market_data([])
        self.assertFalse(res["is_anomaly"])
        self.assertEqual(res["anomaly_score"], 0.0)

    def test_analyze_market_data_normal(self):
        data = [
            {"volume": 1000, "frequency": 1},
            {"volume": 1200, "frequency": 2},
            {"volume": 1100, "frequency": 1}
        ]
        res = self.detector.analyze_market_data(data)
        self.assertFalse(res["is_anomaly"])
        self.assertIn("anomaly_score", res)

    def test_analyze_market_data_high_volume_anomaly(self):
        data = [{"volume": 600000, "frequency": 100}]
        res = self.detector.analyze_market_data(data)
        self.assertTrue(res["is_anomaly"])

    def test_evaluate_insider_risk_low(self):
        data = {"volume": 1000, "anomaly_multiplier": 1.0, "is_insider": False}
        res = self.detector.evaluate_insider_risk(data)
        self.assertEqual(res["risk_level"], "LOW")
        self.assertFalse(res["is_insider_anomaly"])

    def test_evaluate_insider_risk_high(self):
        data = {"volume": 600000, "anomaly_multiplier": 4.0, "is_insider": True}
        res = self.detector.evaluate_insider_risk(data)
        self.assertEqual(res["risk_level"], "HIGH")
        self.assertTrue(res["is_insider_anomaly"])

    def test_process_raw_stream_dict(self):
        data = {"volume": 5000}
        res = self.detector.process_raw_stream(data)
        self.assertEqual(res["status"], "PROCESSED")
        self.assertIn("analysis", res)
        self.assertIn("insider_risk", res)

    def test_process_raw_stream_io(self):
        raw_json = json.dumps({"volume": 700000, "anomaly_multiplier": 5.0})
        stream = io.BytesIO(raw_json.encode("utf-8"))
        res = self.detector.process_raw_stream(stream)
        self.assertEqual(res["status"], "PROCESSED")
        self.assertTrue(res["analysis"]["is_anomaly"])

    def test_persist_anomaly(self):
        record = {"anomaly_id": uuid.uuid4().hex}
        res = self.detector.persist_anomaly(record)
        self.assertTrue(res)

    def test_analyze_and_report_normal(self):
        data = {"volume": 500}
        report = self.detector.analyze_and_report(data)
        self.assertEqual(report["status"], "NORMAL")
        self.assertIn("NORMAL", report["report_summary"])

    def test_analyze_and_report_alert(self):
        data = {"volume": 800000, "is_insider": True}
        report = self.detector.analyze_and_report(data)
        self.assertEqual(report["status"], "ALERT")
        self.assertIn("ALERT", report["report_summary"])


if __name__ == "__main__":
    unittest.main()
