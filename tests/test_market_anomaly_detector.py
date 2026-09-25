import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
import os
from skills.market_anomaly_detector import MarketAnomalyDetector, market_anomaly_detector

class TestMarketAnomalyDetector(unittest.TestCase):
    def setUp(self):
        self.db_path = f"{uuid.uuid4().hex}.db"
        self.detector = MarketAnomalyDetector(db_path=self.db_path)
        self.random_stream = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(1000000, 99999999))
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.severity_level = random.choice(["INFO", "WARNING", "CRITICAL", "FATAL"])
        self.min_threshold = random.uniform(1.0, 100.0)
        self.channels = [uuid.uuid4().hex, uuid.uuid4().hex]

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_detect_anomaly_triggers_both_skills(self):
        anomaly_dict = {"is_anomaly": True, "signature": uuid.uuid4().hex}
        with patch("skills.market_anomaly_detector.MarketInsiderActivityTracker") as mock_tracker_cls, \
             patch("skills.market_anomaly_detector.dispatch_portfolio_alerts") as mock_dispatch:

            mock_tracker_instance = mock_tracker_cls.return_value
            mock_tracker_instance.analyze_activity.return_value = anomaly_dict

            detector = MarketAnomalyDetector(db_path=self.db_path)
            result = detector.detect_anomaly(
                self.random_stream,
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.storage_file,
                self.severity_level,
                self.min_threshold,
                self.channels
            )

            self.assertEqual(result, anomaly_dict)
            mock_tracker_instance.analyze_activity.assert_called_once()
            mock_dispatch.assert_called_once_with(
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.storage_file,
                self.severity_level,
                self.min_threshold,
                self.channels
            )

    def test_detect_anomaly_no_dispatch_on_normal_activity(self):
        normal_dict = {"is_anomaly": False, "signature": uuid.uuid4().hex}
        with patch("skills.market_anomaly_detector.MarketInsiderActivityTracker") as mock_tracker_cls, \
             patch("skills.market_anomaly_detector.dispatch_portfolio_alerts") as mock_dispatch:

            mock_tracker_instance = mock_tracker_cls.return_value
            mock_tracker_instance.analyze_activity.return_value = normal_dict

            detector = MarketAnomalyDetector(db_path=self.db_path)
            result = detector.detect_anomaly(
                self.random_stream,
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.storage_file,
                self.severity_level,
                self.min_threshold,
                self.channels
            )

            self.assertEqual(result, normal_dict)
            mock_tracker_instance.analyze_activity.assert_called_once()
            mock_dispatch.assert_not_called()

    def test_stream_bytes_handling(self):
        raw_bytes = uuid.uuid4().hex.encode('utf-8')
        activity_dict = {"is_anomaly": False}
        with patch("skills.market_anomaly_detector.MarketInsiderActivityTracker") as mock_tracker_cls:
            mock_tracker_instance = mock_tracker_cls.return_value
            mock_tracker_instance.analyze_activity.return_value = activity_dict

            detector = MarketAnomalyDetector()
            res = detector.process_raw_stream_bytes(raw_bytes)
            self.assertEqual(res, activity_dict)
            mock_tracker_instance.analyze_activity.assert_called_once()

    def test_detect_and_dispatch_returns_structured_payload(self):
        anomaly_dict = {"is_anomaly": True, "details": uuid.uuid4().hex}
        dispatch_response = uuid.uuid4().hex
        with patch("skills.market_anomaly_detector.MarketInsiderActivityTracker") as mock_tracker_cls, \
             patch("skills.market_anomaly_detector.dispatch_portfolio_alerts", return_value=dispatch_response) as mock_dispatch:

            mock_tracker_instance = mock_tracker_cls.return_value
            mock_tracker_instance.analyze_activity.return_value = anomaly_dict

            detector = MarketAnomalyDetector(db_path=self.db_path)
            response = detector.detect_and_dispatch(
                self.symbol,
                uuid.uuid4().hex,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.storage_file,
                self.severity_level,
                self.min_threshold,
                self.channels
            )

            self.assertTrue(response["anomaly_detected"])
            self.assertEqual(response["dispatch_status"], dispatch_response)
            self.assertEqual(response["activity_details"], anomaly_dict)
            mock_dispatch.assert_called_once()

    def test_additional_api_methods(self):
        self.assertIsNotNone(market_anomaly_detector)
        detector = MarketAnomalyDetector(db_path=self.db_path)

        # Test analyze_market_feed & evaluate_insider_metrics
        res_feed = detector.analyze_market_feed(b"test_stream")
        self.assertIsInstance(res_feed, dict)

        res_metrics = detector.evaluate_insider_metrics(b"test_stream")
        self.assertIsInstance(res_metrics, dict)

        res_risk = detector.evaluate_insider_risk(b"test_stream")
        self.assertIsInstance(res_risk, dict)

        res_data = detector.analyze_market_data(b"test_stream")
        self.assertIsInstance(res_data, dict)

        res_stream = detector.process_raw_stream(b"test_stream")
        self.assertIsInstance(res_stream, dict)

        # Test persist_anomaly
        signature = uuid.uuid4().hex
        persisted = detector.persist_anomaly(self.symbol, True, signature)
        self.assertTrue(persisted)
