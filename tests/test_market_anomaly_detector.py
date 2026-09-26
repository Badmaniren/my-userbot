import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import requests

from skills.market_anomaly_detector import MarketAnomalyDetector, market_anomaly_detector
from skills import market_parser


class TestMarketAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.detector = MarketAnomalyDetector()
        self.random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.random_exchange = f"EXCHANGE_{uuid.uuid4().hex[:6].upper()}"

    def test_detect_valid_anomaly_data(self):
        random_price = round(random.uniform(10.0, 1000.0), 2)
        random_volume = random.randint(1000, 100000)
        is_anomaly_flag = random.choice([True, False])

        mock_data = {
            "ticker": self.random_ticker,
            "price": random_price,
            "volume": random_volume,
            "anomaly_flag": is_anomaly_flag,
            "exchange": self.random_exchange
        }

        with patch("skills.market_parser.fetch_market_data", return_value=mock_data) as mock_fetch:
            result = self.detector.detect(self.random_ticker)
            mock_fetch.assert_called_once_with(self.random_ticker)

            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertEqual(result["price"], random_price)
            self.assertEqual(result["volume"], random_volume)
            self.assertEqual(result["is_anomaly"], is_anomaly_flag)
            self.assertEqual(result.get("exchange"), self.random_exchange)

    def test_detect_empty_or_invalid_data(self):
        invalid_inputs = [{}, None, [], f"INVALID_{uuid.uuid4().hex[:4]}"]

        for invalid_data in invalid_inputs:
            with patch("skills.market_parser.fetch_market_data", return_value=invalid_data):
                result = self.detector.detect(self.random_ticker)
                self.assertFalse(result["is_anomaly"])
                self.assertEqual(result["ticker"], self.random_ticker)
                self.assertIn("warning", result)

    def test_detect_missing_required_fields(self):
        partial_data = {
            "ticker": self.random_ticker,
            "price": round(random.uniform(1.0, 50.0), 2)
            # missing volume and anomaly_flag
        }

        with patch("skills.market_parser.fetch_market_data", return_value=partial_data):
            result = self.detector.detect(self.random_ticker)
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertEqual(result["warning"], "Missing required fields")

    def test_detect_request_exception(self):
        random_error_msg = f"Network failure {uuid.uuid4().hex}"

        with patch("skills.market_parser.fetch_market_data", side_effect=requests.exceptions.RequestException(random_error_msg)):
            result = self.detector.detect(self.random_ticker)
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["error"], random_error_msg)

    def test_detect_general_exception(self):
        random_error_msg = f"Unexpected error {uuid.uuid4().hex}"

        with patch("skills.market_parser.fetch_market_data", side_effect=Exception(random_error_msg)):
            result = self.detector.detect(self.random_ticker)
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["error"], random_error_msg)

    def test_analyze_stream_with_valid_stream(self):
        random_bytes = f"stream_data_{uuid.uuid4().hex}".encode("utf-8")
        mock_stream = io.BytesIO(random_bytes)

        with patch("skills.market_parser.get_raw_stream", return_value=mock_stream) as mock_stream_func:
            result = self.detector.analyze_stream(self.random_exchange)
            mock_stream_func.assert_called_once_with(self.random_exchange)

            self.assertEqual(result["exchange"], self.random_exchange)
            self.assertEqual(result["status"], "analyzed")

    def test_analyze_stream_with_none_stream(self):
        with patch("skills.market_parser.get_raw_stream", return_value=None):
            result = self.detector.analyze_stream(self.random_exchange)
            self.assertEqual(result["exchange"], self.random_exchange)
            self.assertEqual(result["status"], "analyzed")

    def test_market_anomaly_detector_function_high_volume(self):
        random_price = round(random.uniform(50.0, 500.0), 2)
        random_volume = random.randint(50001, 200000)
        random_symbol = f"SYM_{uuid.uuid4().hex[:5].upper()}"

        payload = {
            "volume": random_volume,
            "price": random_price,
            "symbol": random_symbol
        }

        result = market_anomaly_detector(payload)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["symbol"], random_symbol)
        self.assertEqual(result["volume"], random_volume)
        self.assertEqual(result["price"], random_price)
        self.assertEqual(result["anomaly_score"], float(random_volume) / 10000.0)

    def test_market_anomaly_detector_function_low_volume(self):
        random_price = round(random.uniform(1.0, 49.99), 2)
        random_volume = random.randint(0, 50000)
        random_ticker_key = f"TICK_{uuid.uuid4().hex[:5].upper()}"

        payload = {
            "volume": random_volume,
            "price": random_price,
            "ticker": random_ticker_key
        }

        result = market_anomaly_detector(payload)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["symbol"], random_ticker_key)
        self.assertEqual(result["volume"], random_volume)
        self.assertEqual(result["price"], random_price)
        self.assertEqual(result["anomaly_score"], 0.1)


if __name__ == "__main__":
    unittest.main()