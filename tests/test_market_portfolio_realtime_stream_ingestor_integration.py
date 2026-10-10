import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_realtime_stream_ingestor import market_portfolio_realtime_stream_ingestor

class TestMarketPortfolioRealtimeStreamIngestorIntegration(unittest.TestCase):
    def test_realtime_stream_ingestor_integration(self):
        random_event_id = str(uuid.uuid4())
        random_ticker = f"TICK_{random.randint(1000, 9999)}"
        random_price = round(random.uniform(10.0, 1500.0), 2)
        
        payload = {
            "event_id": random_event_id,
            "ticker": random_ticker,
            "price": random_price,
            "volume": random.randint(100, 10000)
        }
        
        output_dir = f"test_audit_storage_{uuid.uuid4()}"
        output_path = os.path.join(output_dir, "stream_audit.json")
        
        try:
            result = market_portfolio_realtime_stream_ingestor(payload, output_path)
            
            self.assertEqual(result.get("status"), "SUCCESS")
            self.assertEqual(result.get("processed_id"), random_event_id)
            
            self.assertTrue(os.path.exists(output_path))
            
            with open(output_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                
            self.assertEqual(saved_data.get("event_id"), random_event_id)
            self.assertEqual(saved_data.get("ticker"), random_ticker)
            self.assertEqual(saved_data.get("price"), random_price)
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
            if os.path.exists(output_dir):
                os.rmdir(output_dir)

if __name__ == "__main__":
    unittest.main()