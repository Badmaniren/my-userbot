import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_realtime_anomaly_reactor_v2 import (
    market_portfolio_realtime_anomaly_reactor_v2,
    RealtimeAnomalyReactor
)

class TestMarketPortfolioRealtimeAnomalyReactorV2Integration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_output_dir"
        os.makedirs(self.test_dir, exist_ok=True)
        self.output_file = os.path.join(self.test_dir, f"anomaly_report_{uuid.uuid4()}.json")
        
        self.random_ticker = f"TICKER_{random.randint(1000, 9999)}"
        self.random_stream_source = f"wss://stream.exchange-{random.randint(100, 999)}.org/feed"
        
        self.payload = {
            "stream_source": self.random_stream_source,
            "ticker": self.random_ticker,
            "price": round(random.uniform(10.0, 1500.0), 2),
            "volume": random.randint(100, 50000),
            "timestamp": uuid.uuid4().hex
        }

    def tearDown(self):
        if os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
            except OSError:
                pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_market_portfolio_realtime_anomaly_reactor_v2_integration(self):
        result = market_portfolio_realtime_anomaly_reactor_v2(self.payload, self.output_file)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("ticker"), self.random_ticker)
        self.assertIn("ingestion", result)
        self.assertIn("detection", result)
        
        self.assertTrue(os.path.exists(self.output_file), "Файл отчета не был создан.")
        
        with open(self.output_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            
        self.assertEqual(file_data.get("status"), "success")
        self.assertEqual(file_data.get("ticker"), self.random_ticker)
        self.assertIn("ingestion", file_data)
        self.assertIn("detection", file_data)

    def test_realtime_anomaly_reactor_class_methods(self):
        reactor = RealtimeAnomalyReactor(stream_source=self.random_stream_source)
        
        process_res = reactor.process_stream_payload(self.payload, self.output_file)
        self.assertIsInstance(process_res, dict)
        self.assertTrue(process_res.get("reactor_status"))
        self.assertIn("ingestion", process_res)
        self.assertIn("anomaly_analysis", process_res)
        
        context = {
            "session_id": str(uuid.uuid4()),
            "ticker": self.random_ticker
        }
        live_res = reactor.start_live_monitoring(context)
        self.assertIsInstance(live_res, dict)
        self.assertIn("analysis", live_res)

if __name__ == "__main__":
    unittest.main()