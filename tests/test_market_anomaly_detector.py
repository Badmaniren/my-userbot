import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io
import requests

from skills.market_anomaly_detector import MarketAnomalyDetector, market_anomaly_detector
from skills import market_parser


class TestMarketAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.detector = MarketAnomalyDetector()
        self.random_ticker = f"TICKER_{uuid.uuid4().hex[:6]}"
        self.random_exchange = f"EXCH_{uuid.uuid4().hex[:6]}"
        self.random_volume = random.randint(100, 100000)
        self.random_price = round(random.uniform(1.0, 1500.0), 2)

    def test_detect_empty_or_invalid_data(self):
        with patch("skills.market_parser.fetch_market_data") as mock_fetch:
            mock_fetch.return_value = None
            result = self.detector.detect(self.random_ticker)
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertIn("warning", result)

            mock_fetch.return_value = f"invalid_type_{uuid.uuid4().hex}"
            result_str = self.detector.detect(self.random_ticker)
            self.assertFalse(result_str["is_anomaly"])
            self.assertIn("warning", result_str)

    def test_detect_missing_required_fields(self):
        with patch("skills.market_parser.fetch_market_data") as mock_fetch:
            partial_data = {
                "ticker": self.random_ticker,
                "volume": self.random_volume
            }
            mock_fetch.return_value = partial_data
            result = self.detector.detect(self.random_ticker)
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertEqual(result["warning"], "Missing required fields")

    def test_detect_successful_anomaly_detection(self):
        with patch("skills.market_parser.fetch_market_data") as mock_fetch:
            is_anom = random.choice([True, False])
            complete_data = {
                "ticker": self.random_ticker,
                "anomaly_flag": is_anom,
                "volume": self.random_volume,
                "price": self.random_price,
                "exchange": self.random_exchange
            }
            mock_fetch.return_value = complete_data
            result = self.detector.detect(self.random_ticker)

            self.assertEqual(result["is_anomaly"], is_anom)
            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertEqual(result["volume"], self.random_volume)
            self.assertEqual(result["price"], self.random_price)
            self.assertEqual(result["exchange"], self.random_exchange)

    def test_detect_request_exception(self):
        with patch("skills.market_parser.fetch_market_data") as mock_fetch:
            err_msg = f"network_error_{uuid.uuid4().hex}"
            mock_fetch.side_effect = requests.exceptions.RequestException(err_msg)
            result = self.detector.detect(self.random_ticker)

            self.assertFalse(result["is_anomaly"])
            self.assertIn(err_msg, result["error"])

    def test_detect_general_exception(self):
        with patch("skills.market_parser.fetch_market_data") as mock_fetch:
            err_msg = f"critical_fault_{uuid.uuid4().hex}"
            mock_fetch.side_effect = Exception(err_msg)
            result = self.detector.detect(self.random_ticker)

            self.assertFalse(result["is_anomaly"])
            self.assertIn(err_msg, result["error"])

    def test_analyze_stream_with_valid_stream(self):
        with patch("skills.market_parser.get_raw_stream") as mock_stream:
            payload = f"stream_data_{uuid.uuid4().hex}".encode("utf-8")
            mock_io = io.BytesIO(payload)
            mock_stream.return_value = mock_io

            result = self.detector.analyze_stream(self.random_exchange)
            self.assertEqual(result["exchange"], self.random_exchange)
            self.assertEqual(result["status"], "analyzed")

    def test_analyze_stream_with_no_stream(self):
        with patch("skills.market_parser.get_raw_stream") as mock_stream:
            mock_stream.return_value = None

            result = self.detector.analyze_stream(self.random_exchange)
            self.assertEqual(result["exchange"], self.random_exchange)
            self.assertEqual(result["status"], "analyzed")

    def test_market_anomaly_detector_function_high_volume(self):
        high_vol = random.randint(50001, 200000)
        data = {
            "volume": high_vol,
            "price": self.random_price,
            "ticker": self.random_ticker
        }
        res = market_anomaly_detector(data)
        self.assertTrue(res["is_anomaly"])
        self.assertEqual(res["symbol"], self.random_ticker)
        self.assertEqual(res["volume"], high_vol)
        self.assertEqual(res["price"], self.random_price)
        self.assertAlmostEqual(res["anomaly_score"], float(high_vol) / 10000.0)

    def test_market_anomaly_detector_function_low_volume(self):
        low_vol = random.randint(0, 50000)
        symbol_key = random.choice(["symbol", "ticker"])
        data = {
            "volume": low_vol,
            "price": self.random_price,
            symbol_key: self.random_ticker
        }
        res = market_anomaly_detector(data)
        self.assertFalse(res["is_anomaly"])
        self.assertEqual(res["symbol"], self.random_ticker)
        self.assertEqual(res["volume"], low_vol)
        self.assertEqual(res["price"], self.random_price)
        self.assertEqual(res["anomaly_score"], 0.1)


if __name__ == "__main__":
    unittest.main()