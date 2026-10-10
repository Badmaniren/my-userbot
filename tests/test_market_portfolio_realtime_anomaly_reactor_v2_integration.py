import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_realtime_anomaly_reactor_v2 import market_portfolio_realtime_anomaly_reactor_v2

class TestMarketPortfolioRealtimeAnomalyReactorV2Integration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.output_path = os.path.join(self.test_dir.name, f"anomaly_report_{uuid.uuid4()}.json")
        self.ticker = f"TICKER_{random.randint(1000, 9999)}"
        self.exchange = f"EXCHANGE_{uuid.uuid4().hex[:6]}"
        self.payload = {
            "stream_source": self.exchange,
            "ticker": self.ticker,
            "initial_price": round(random.uniform(10.0, 1000.0), 2),
            "volume": random.randint(100, 50000)
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_realtime_anomaly_reactor_integration(self):
        result = market_portfolio_realtime_anomaly_reactor_v2(self.payload, self.output_path)
        
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result.get("ticker"), self.ticker)
        self.assertTrue(os.path.exists(self.output_path), "Файл отчета об аномалиях не был создан.")
        
        with open(self.output_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(len(content), 0, "Файл отчета пуст.")

if __name__ == "__main__":
    unittest.main()