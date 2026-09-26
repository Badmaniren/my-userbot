import unittest
from unittest.mock import patch
import random
import uuid
import io
import requests
from skills.market_anomaly_detector import MarketAnomalyDetector, market_anomaly_detector

class TestMarketAnomalyDetector(unittest.TestCase):
    def setUp(self):
        self.detector = MarketAnomalyDetector()
        self.random_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.random_exchange = f"EX_{uuid.uuid4().hex[:6].upper()}"
        self.random_volume = random.randint(1000, 100000)
        self.random_price = round(random.uniform(1.0, 1000.0), 2)

    def test_detect_success(self):
        mock_data = {
            "ticker": self.random_ticker,
            "anomaly_flag": True,
            "volume": self.random_volume,
            "price": self.random_price,
            "exchange": self.random_exchange
        }
        with patch("skills.market_anomaly_detector.market_parser.fetch_market_data", return_value=mock_data) as mock_fetch:
            result = self.detector.detect(self.random_ticker)
            mock_fetch.assert_called_once_with(self.random_ticker)
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertEqual(result["volume"], self.random_volume)
            self.assertEqual(result["price"], self.random_price)
            self.assertEqual(result["exchange"], self.random_exchange)

    def test_detect_empty_or_invalid_data(self):
        for invalid_data in [None, {}, []]:
            with patch("skills.market_anomaly_detector.market_parser.fetch_market_data", return_value=invalid_data):
                result = self.detector.detect(self.random_ticker)
                self.assertFalse(result["is_anomaly"])
                self.assertEqual(result["ticker"], self.random_ticker)
                self.assertIn("warning", result)

    def test_detect_missing_fields(self):
        incomplete_data = {
            "ticker": self.random_ticker,
            "volume": self.random_volume
        }
        with patch("skills.market_anomaly_detector.market_parser.fetch_market_data", return_value=incomplete_data):
            result = self.detector.detect(self.random_ticker)
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertEqual(result["warning"], "Missing required fields")

    def test_detect_request_exception(self):
        err_msg = f"Network failure {uuid.uuid4().hex[:4]}"
        with patch("skills.market_anomaly_detector.market_parser.fetch_market_data", side_effect=requests.exceptions.RequestException(err_msg)):
            result = self.detector.detect(self.random_ticker)
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["error"], err_msg)

    def test_detect_generic_exception(self):
        err_msg = f"Fatal error {uuid.uuid4().hex[:4]}"
        with patch("skills.market_anomaly_detector.market_parser.fetch_market_data", side_effect=Exception(err_msg)):
            result = self.detector.detect(self.random_ticker)
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["error"], err_msg)

    def test_analyze_stream(self):
        random_bytes = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)
        with patch("skills.market_anomaly_detector.market_parser.get_raw_stream", return_value=mock_stream) as mock_get_stream:
            result = self.detector.analyze_stream(self.random_exchange)
            mock_get_stream.assert_called_once_with(self.random_exchange)
            self.assertEqual(result["exchange"], self.random_exchange)
            self.assertEqual(result["status"], "analyzed")

    def test_market_anomaly_detector_function_high_volume(self):
        high_vol = random.randint(50001, 200000)
        data = {
            "volume": high_vol,
            "price": self.random_price,
            "symbol": self.random_ticker
        }
        result = market_anomaly_detector(data)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["symbol"], self.random_ticker)
        self.assertEqual(result["volume"], high_vol)
        self.assertEqual(result["price"], self.random_price)
        self.assertEqual(result["anomaly_score"], float(high_vol) / 10000.0)

    def test_market_anomaly_detector_function_low_volume(self):
        low_vol = random.randint(0, 50000)
        data = {
            "volume": low_vol,
            "price": self.random_price,
            "ticker": self.random_ticker
        }
        result = market_anomaly_detector(data)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["symbol"], self.random_ticker)
        self.assertEqual(result["volume"], low_vol)
        self.assertEqual(result["price"], self.random_price)
        self.assertEqual(result["anomaly_score"], 0.1)

if __name__ == "__main__":
    unittest.main()