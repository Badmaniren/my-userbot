import unittest
import uuid
import random
from skills.market_anomaly_detector import MarketAnomalyDetector, market_anomaly_detector
from skills import market_parser

class TestMarketAnomalyDetectorIntegration(unittest.TestCase):
    def setUp(self):
        self.detector = MarketAnomalyDetector()
        self.test_ticker = f"TICKER_{uuid.uuid4().hex[:8].upper()}"
        self.test_exchange = f"EXCH_{uuid.uuid4().hex[:6].upper()}"
        self.random_volume = random.randint(1000, 100000)
        self.random_price = round(random.uniform(10.0, 1500.0), 2)

    def test_market_anomaly_detector_class_integration(self):
        original_fetch = getattr(market_parser, "fetch_market_data", None)
        
        try:
            market_parser.fetch_market_data = lambda ticker: {
                "ticker": ticker,
                "anomaly_flag": True,
                "volume": self.random_volume,
                "price": self.random_price,
                "exchange": self.test_exchange
            }
            
            result = self.detector.detect(self.test_ticker)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("ticker"), self.test_ticker)
            self.assertTrue(result.get("is_anomaly"))
            self.assertEqual(result.get("volume"), self.random_volume)
            self.assertEqual(result.get("price"), self.random_price)
            self.assertEqual(result.get("exchange"), self.test_exchange)
            
        finally:
            if original_fetch is not None:
                market_parser.fetch_market_data = original_fetch
            elif hasattr(market_parser, "fetch_market_data"):
                delattr(market_parser, "fetch_market_data")

    def test_market_anomaly_detector_function_integration(self):
        input_data = {
            "symbol": self.test_ticker,
            "volume": self.random_volume,
            "price": self.random_price
        }
        
        result = market_anomaly_detector(input_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("symbol"), self.test_ticker)
        self.assertEqual(result.get("volume"), self.random_volume)
        self.assertEqual(result.get("price"), self.random_price)
        self.assertEqual(result.get("is_anomaly"), self.random_volume > 50000)
        self.assertIsInstance(result.get("anomaly_score"), float)

    def test_analyze_stream_integration(self):
        class DummyStream:
            def read(self):
                return b"data_stream_chunk"

        original_stream = getattr(market_parser, "get_raw_stream", None)

        try:
            market_parser.get_raw_stream = lambda exchange: DummyStream()
            
            result = self.detector.analyze_stream(self.test_exchange)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("exchange"), self.test_exchange)
            self.assertEqual(result.get("status"), "analyzed")
            
        finally:
            if original_stream is not None:
                market_parser.get_raw_stream = original_stream
            elif hasattr(market_parser, "get_raw_stream"):
                delattr(market_parser, "get_raw_stream")

if __name__ == "__main__":
    unittest.main()