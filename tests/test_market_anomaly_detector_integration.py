import unittest
import uuid
import random
from skills import market_anomaly_detector
from skills import market_parser

class TestMarketAnomalyDetectorIntegration(unittest.TestCase):
    def test_market_anomaly_detector_real_integration(self):
        random_ticker = f"TICKER_{uuid.uuid4().hex[:8].upper()}"
        random_volume = random.randint(1000, 100000)
        random_price = round(random.uniform(10.0, 1000.0), 2)
        
        original_fetch = getattr(market_parser, "fetch_market_data", None)
        
        try:
            market_parser.fetch_market_data = lambda t: {
                "ticker": t,
                "volume": random_volume,
                "price": random_price,
                "anomaly_flag": random_volume > 50000,
                "exchange": "NYSE"
            }
            
            detector = market_anomaly_detector.MarketAnomalyDetector()
            result = detector.detect(random_ticker)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("ticker"), random_ticker)
            self.assertEqual(result.get("volume"), random_volume)
            self.assertEqual(result.get("price"), random_price)
            self.assertIn("is_anomaly", result)
            
            payload = {
                "symbol": random_ticker,
                "volume": random_volume,
                "price": random_price
            }
            functional_result = market_anomaly_detector.market_anomaly_detector(payload)
            
            self.assertIsInstance(functional_result, dict)
            self.assertEqual(functional_result.get("symbol"), random_ticker)
            self.assertEqual(functional_result.get("volume"), random_volume)
            self.assertEqual(functional_result.get("price"), random_price)
            self.assertIsInstance(functional_result.get("anomaly_score"), float)
            
        finally:
            if original_fetch is not None:
                market_parser.fetch_market_data = original_fetch

if __name__ == "__main__":
    unittest.main()