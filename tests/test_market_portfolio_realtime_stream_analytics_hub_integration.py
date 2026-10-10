import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_realtime_stream_ingestor import market_portfolio_realtime_stream_ingestor, start_new
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics
from skills.market_portfolio_realtime_stream_analytics_hub import process_realtime_stream_hub

class TestMarketPortfolioRealtimeStreamAnalyticsHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4().hex}.json")
        self.output_path = os.path.join(self.test_dir.name, f"output_{uuid.uuid4().hex}.json")
        
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.volume = random.randint(100, 10000)
        self.payload = {
            "symbol": self.symbol,
            "price": self.price,
            "volume": self.volume,
            "timestamp": uuid.uuid1().hex
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_realtime_stream_analytics_hub_composition(self):
        ingest_result = market_portfolio_realtime_stream_ingestor(self.payload, self.output_path)
        self.assertIsInstance(ingest_result, dict)
        self.assertTrue(os.path.exists(self.output_path))

        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        self.assertIsNotNone(analytics)

        hub_result = process_realtime_stream_hub(self.output_path, self.storage_file, self.symbol)
        self.assertIsInstance(hub_result, dict)
        self.assertIn("metrics", hub_result)

if __name__ == "__main__":
    unittest.main()