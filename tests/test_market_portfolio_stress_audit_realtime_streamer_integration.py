import unittest
import sys
import io
import uuid
import random
from skills import db_storage
from skills.market_portfolio_stress_audit_realtime_streamer import MarketPortfolioStressAuditRealtimeStreamer

class TestMarketPortfolioStressAuditRealtimeStreamerIntegration(unittest.TestCase):

    def setUp(self):
        self.streamer = MarketPortfolioStressAuditRealtimeStreamer(db_storage=db_storage)
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.metric_name = f"var_drop_{random.randint(100, 999)}"
        self.metric_value = round(random.uniform(5.0, 95.0), 2)

    def test_stream_and_persist_integration(self):
        test_line = f"{self.portfolio_id}:{self.metric_name}:{self.metric_value}\n"
        sys.stdin = io.StringIO(test_line)

        success = self.streamer.stream_and_persist(self.portfolio_id)
        self.assertTrue(success, "Streamer должен успешно распарсить и сохранить метрику из потока")

        audit_data = self.streamer.get_live_audit_metrics(self.portfolio_id)
        self.assertIsInstance(audit_data, dict)

    def test_stream_audit_metrics_generation(self):
        result = self.streamer.stream_audit_metrics(self.portfolio_id)
        self.assertIn("stream_id", result)
        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertTrue(uuid.UUID(result["stream_id"]), "stream_id должен быть валидным UUID")

if __name__ == '__main__':
    unittest.main()