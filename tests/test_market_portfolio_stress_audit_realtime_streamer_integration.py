import unittest
import uuid
import random
import os
from skills.db_storage import db_storage
from skills.market_portfolio_stress_audit_realtime_streamer import market_portfolio_stress_audit_realtime_streamer

class TestMarketPortfolioStressAuditRealtimeStreamerIntegration(unittest.TestCase):
    def test_realtime_streamer_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_stress_level = round(random.uniform(10.0, 95.0), 2)
        
        db_storage.save_portfolio_metric(portfolio_id, "stress_level", initial_stress_level)
        
        streamer_output = market_portfolio_stress_audit_realtime_streamer.stream_audit_metrics(
            portfolio_id=portfolio_id
        )
        
        self.assertIsNotNone(streamer_output)
        self.assertIn("stream_id", streamer_output)
        
        retrieved_data = db_storage.get_portfolio_metric(portfolio_id, "stress_level")
        self.assertEqual(retrieved_data, initial_stress_level)

if __name__ == "__main__":
    unittest.main()