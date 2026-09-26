import unittest
import uuid
import random
from skills import market_anomaly_detector
from skills import market_parser

class TestMarketAnomalyDetectorIntegration(unittest.TestCase):
    def test_market_anomaly_detector_integration_flow(self):
        random_ticker = f"TICKER_{uuid.uuid4().hex[:8]}"
        random_volume = random.randint(1000, 100000)
        random_price = round(random.uniform(10.0, 1500.0), 2)
        
        test_payload = {
            "ticker": random_ticker,
            "symbol": random_ticker,
            "volume": random_volume,
            "price": random_price,
            "anomaly_flag": random_volume > 50000,
            "exchange": "TEST_EXCHANGE"
        }

        if hasattr(market_parser, "fetch_market_data"):
            original_fetch = market_parser.fetch_market_data
            market_parser.fetch_market_data = lambda t: test_payload if t == random_ticker else {}

        try:
            detector_class = getattr(market_anomaly_detector, "MarketAnomalyDetector", None)
            if detector_class:
                instance = detector_class()
                if hasattr(instance, "detect"):
                    result = instance.detect(random_ticker)
                    self.assertIsInstance(result, dict)
                    self.assertIn("is_anomaly", result)
                    self.assertEqual(result.get("ticker"), random_ticker)

            functional_detector = getattr(market_anomaly_detector, "market_anomaly_detector", None)
            if functional_detector:
                func_result = functional_detector(test_payload)
                self.assertIsInstance(func_result, dict)
                self.assertEqual(func_result.get("symbol"), random_ticker)
                self.assertEqual(func_result.get("volume"), random_volume)
                self.assertEqual(func_result.get("price"), random_price)
                expected_anomaly = random_volume > 50000
                self.assertEqual(func_result.get("is_anomaly"), expected_anomaly)

        finally:
            if hasattr(market_parser, "fetch_market_data") and 'original_fetch' in locals():
                market_parser.fetch_market_data = original_fetch

if __name__ == "__main__":
    unittest.main()