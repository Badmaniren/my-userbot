import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import requests

from skills.market_anomaly_detector import MarketAnomalyDetector

class TestMarketAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.detector = MarketAnomalyDetector()
        self.random_ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_exchange = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.random_error_msg = uuid.uuid4().hex
        self.random_volume = random.randint(10000, 99999999)
        self.random_price = round(random.uniform(1.0, 1000.0), 2)

    def test_detect_anomaly_success(self):
        mock_market_parser = MagicMock()
        expected_data = {
            "ticker": self.random_ticker,
            "exchange": self.random_exchange,
            "volume": self.random_volume,
            "price": self.random_price,
            "anomaly_flag": True
        }
        mock_market_parser.fetch_market_data.return_value = expected_data

        with patch('skills.market_anomaly_detector.market_parser', mock_market_parser):
            result = self.detector.detect(self.random_ticker)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["ticker"], self.random_ticker)
        self.assertEqual(result["volume"], self.random_volume)
        self.assertEqual(result["price"], self.random_price)
        mock_market_parser.fetch_market_data.assert_called_once_with(self.random_ticker)

    def test_detect_anomaly_no_anomaly(self):
        mock_market_parser = MagicMock()
        normal_volume = random.randint(100, 5000)
        expected_data = {
            "ticker": self.random_ticker,
            "exchange": self.random_exchange,
            "volume": normal_volume,
            "price": self.random_price,
            "anomaly_flag": False
        }
        mock_market_parser.fetch_market_data.return_value = expected_data

        with patch('skills.market_anomaly_detector.market_parser', mock_market_parser):
            result = self.detector.detect(self.random_ticker)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["volume"], normal_volume)
        mock_market_parser.fetch_market_data.assert_called_once_with(self.random_ticker)

    def test_detect_anomaly_parser_error_handling(self):
        mock_market_parser = MagicMock()
        mock_market_parser.fetch_market_data.side_effect = requests.exceptions.RequestException(self.random_error_msg)

        with patch('skills.market_anomaly_detector.market_parser', mock_market_parser):
            result = self.detector.detect(self.random_ticker)

        self.assertIn("error", result)
        self.assertIn(self.random_error_msg, result["error"])
        self.assertFalse(result.get("is_anomaly", False))

    def test_stream_volume_spike_detector_with_io(self):
        mock_market_parser = MagicMock()
        random_payload = uuid.uuid4().bytes + str(self.random_volume).encode('utf-8')
        mock_stream = io.BytesIO(random_payload)
        
        mock_market_parser.get_raw_stream.return_value = mock_stream

        with patch('skills.market_anomaly_detector.market_parser', mock_market_parser):
            stream_result = self.detector.analyze_stream(self.random_exchange)

        self.assertIsNotNone(stream_result)
        self.assertTrue(isinstance(stream_result, dict))
        mock_market_parser.get_raw_stream.assert_called_once_with(self.random_exchange)

    def test_anomaly_detector_missing_data_fields(self):
        mock_market_parser = MagicMock()
        malformed_data = {
            "ticker": self.random_ticker,
            "malformed_key": uuid.uuid4().hex
        }
        mock_market_parser.fetch_market_data.return_value = malformed_data

        with patch('skills.market_anomaly_detector.market_parser', mock_market_parser):
            result = self.detector.detect(self.random_ticker)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result.get("ticker"), self.random_ticker)
        self.assertIn("warning", result)

if __name__ == '__main__':
    unittest.main()