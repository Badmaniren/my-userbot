import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_realtime_stream_ingestor import market_portfolio_realtime_stream_ingestor

class IntegrationTestMarketPortfolioRealtimeStreamIngestor(unittest.TestCase):
    def test_stream_ingestor_integration(self):
        random_id = str(uuid.uuid4())
        random_price = round(random.uniform(10.0, 5000.0), 2)
        random_volume = random.randint(100, 100000)
        
        test_payload = {
            "event_id": random_id,
            "symbol": f"TEST_{random.randint(100, 999)}",
            "price": random_price,
            "volume": random_volume,
            "timestamp": random.randint(1600000000, 1700000000)
        }

        temp_dir = tempfile.gettempdir()
        target_file = os.path.join(temp_dir, f"ingest_audit_{random_id}.log")

        try:
            result = market_portfolio_realtime_stream_ingestor(
                payload=test_payload,
                output_path=target_file
            )

            self.assertIsNotNone(result, "Модуль не должен возвращать None")
            
            if isinstance(result, dict):
                self.assertIn("status", result)
                self.assertEqual(result.get("processed_id"), random_id)
            elif isinstance(result, str):
                self.assertIn(random_id, result)

            self.assertTrue(os.path.exists(target_file), "Интеграционный модуль должен зафиксировать поток в хранилище/файле")
            
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(random_id, content)
                self.assertIn(str(random_price), content)

        finally:
            if os.path.exists(target_file):
                os.remove(target_file)

if __name__ == "__main__":
    unittest.main()