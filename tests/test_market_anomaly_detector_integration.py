import unittest
import uuid
import random
from skills import market_parser
from skills.market_anomaly_detector import MarketAnomalyDetector, market_anomaly_detector

class TestMarketAnomalyDetectorIntegration(unittest.TestCase):
    def setUp(self):
        self.detector = MarketAnomalyDetector()
        self.test_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.random_volume = random.randint(1000, 100000)
        self.random_price = round(random.uniform(10.0, 1500.0), 2)

    def test_detect_integration_with_real_parser(self):
        result = self.detector.detect(self.test_ticker)
        self.assertIsInstance(result, dict)
        self.assertIn("is_anomaly", result)
        self.assertIn("ticker", result)
        self.assertEqual(result["ticker"], self.test_ticker)

    def test_analyze_stream_integration(self):
        exchange_name = f"EXCHANGE_{uuid.uuid4().hex[:4].upper()}"
        result = self.detector.analyze_stream(exchange_name)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("exchange"), exchange_name)
        self.assertEqual(result.get("status"), "analyzed")

    def test_functional_detector_with_random_data(self):
        input_data = {
            "ticker": self.test_ticker,
            "volume": self.random_volume,
            "price": self.random_price
        }
        result = market_anomaly_detector(input_data)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], self.test_ticker)
        self.assertEqual(result["volume"], self.random_volume)
        self.assertEqual(result["price"], self.random_price)
        self.assertIsInstance(result["is_anomaly"], bool)
        self.assertIsInstance(result["anomaly_score"], float)

if __name__ == "__main__":
    unittest.main()