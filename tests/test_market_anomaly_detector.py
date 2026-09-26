import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
requests = __import__('requests')

from skills.market_anomaly_detector import MarketAnomalyDetector, market_anomaly_detector
from skills import market_parser

class TestMarketAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.detector = MarketAnomalyDetector()
        self.random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.random_exchange = f"EXCH_{uuid.uuid4().hex[:6].upper()}"

    def test_detect_empty_or_invalid_data(self):
        invalid_inputs = [None, {}, [], ""]
        for invalid_data in invalid_inputs:
            with patch("skills.market_parser.fetch_market_data", return_value=invalid_data):
                result = self.detector.detect(self.random_ticker)
                self.assertFalse(result["is_anomaly"])
                self.assertEqual(result["ticker"], self.random_ticker)
                self.assertIn("warning", result)

    def test_detect_missing_required_fields(self):
        partial_data = {
            "ticker": self.random_ticker,
            "anomaly_flag": random.choice([True, False])
        }
        with patch("skills.market_parser.fetch_market_data", return_value=partial_data):
            result = self.detector.detect(self.random_ticker)
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertEqual(result["warning"], "Missing required fields")

    def test_detect_valid_anomaly_data(self):
        expected_price = round(random.uniform(10.0, 1500.0), 2)
        expected_volume = random.randint(1000, 100000)
        expected_flag = random.choice([True, False])
        
        valid_data = {
            "ticker": self.random_ticker,
            "anomaly_flag": expected_flag,
            "volume": expected_volume,
            "price": expected_price,
            "exchange": self.random_exchange
        }
        with patch("skills.market_parser.fetch_market_data", return_value=valid_data):
            result = self.detector.detect(self.random_ticker)
            self.assertEqual(result["is_anomaly"], expected_flag)
            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertEqual(result["volume"], expected_volume)
            self.assertEqual(result["price"], expected_price)
            self.assertEqual(result["exchange"], self.random_exchange)

    def test_detect_request_exception(self):
        random_error_msg = f"Network Error {uuid.uuid4().hex[:8]}"
        with patch("skills.market_parser.fetch_market_data", side_effect=requests.exceptions.RequestException(random_error_msg)):
            result = self.detector.detect(self.random_ticker)
            self.assertFalse(result["is_anomaly"])
            self.assertIn(random_error_msg, result["error"])

    def test_detect_generic_exception(self):
        random_error_msg = f"Critical Failure {uuid.uuid4().hex[:8]}"
        with patch("skills.market_parser.fetch_market_data", side_effect=Exception(random_error_msg)):
            result = self.detector.detect(self.random_ticker)
            self.assertFalse(result["is_anomaly"])
            self.assertIn(random_error_msg, result["error"])

    def test_analyze_stream_with_valid_stream(self):
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        mock_stream = io.BytesIO(random_bytes)
        with patch("skills.market_parser.get_raw_stream", return_value=mock_stream):
            result = self.detector.analyze_stream(self.random_exchange)
            self.assertEqual(result["exchange"], self.random_exchange)
            self.assertEqual(result["status"], "analyzed")

    def test_analyze_stream_without_read_attribute(self):
        mock_stream = object()
        with patch("skills.market_parser.get_raw_stream", return_value=mock_stream):
            result = self.detector.analyze_stream(self.random_exchange)
            self.assertEqual(result["exchange"], self.random_exchange)
            self.assertEqual(result["status"], "analyzed")

    def test_market_anomaly_detector_standalone_low_volume(self):
        low_volume = random.randint(0, 50000)
        price = round(random.uniform(1.0, 500.0), 2)
        payload = {
            "volume": low_volume,
            "price": price,
            "symbol": self.random_ticker
        }
        res = market_anomaly_detector(payload)
        self.assertFalse(res["is_anomaly"])
        self.assertEqual(res["anomaly_score"], 0.1)
        self.assertEqual(res["symbol"], self.random_ticker)
        self.assertEqual(res["volume"], low_volume)
        self.assertEqual(res["price"], price)

    def test_market_anomaly_detector_standalone_high_volume(self):
        high_volume = random.randint(50001, 200000)
        price = round(random.uniform(1.0, 500.0), 2)
        payload = {
            "volume": high_volume,
            "price": price,
            "ticker": self.random_ticker
        }
        res = market_anomaly_detector(payload)
        self.assertTrue(res["is_anomaly"])
        self.assertEqual(res["anomaly_score"], float(high_volume) / 10000.0)
        self.assertEqual(res["symbol"], self.random_ticker)
        self.assertEqual(res["volume"], high_volume)
        self.assertEqual(res["price"], price)

if __name__ == "__main__":
    unittest.main()