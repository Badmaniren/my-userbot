import unittest
import uuid
import random
import sys
import io
from skills import db_storage
from skills.market_portfolio_stress_audit_realtime_streamer import MarketPortfolioStressAuditRealtimeStreamer

class TestMarketPortfolioStressAuditRealtimeStreamerIntegration(unittest.TestCase):
    def setUp(self):
        self.streamer = MarketPortfolioStressAuditRealtimeStreamer(db_storage=db_storage)
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.metric_name = f"var_drop_{random.randint(100, 999)}"
        self.metric_value = round(random.uniform(1.5, 99.9), 2)

    def test_stream_and_persist_integration(self):
        test_line = f"{self.portfolio_id}:{self.metric_name}:{self.metric_value}\n"
        original_stdin = sys.stdin
        sys.stdin = io.StringIO(test_line)
        try:
            result = self.streamer.stream_and_persist(self.portfolio_id)
            self.assertTrue(result, "Поток должен успешно обработать строку с совпадающим ID портфеля")
            
            audit_data = self.streamer.get_live_audit_metrics(self.portfolio_id)
            self.assertIsInstance(audit_data, dict, "Хранилище должно возвращать словарь с метриками аудита")
        finally:
            sys.stdin = original_stdin

    def test_stream_audit_metrics_generation(self):
        rand_portfolio = f"p_{uuid.uuid4().hex}"
        metrics = self.streamer.stream_audit_metrics(rand_portfolio)
        self.assertIn("stream_id", metrics)
        self.assertIn("portfolio_id", metrics)
        self.assertEqual(metrics["portfolio_id"], rand_portfolio)
        self.assertTrue(len(metrics["stream_id"]) > 0)

    def test_invalid_input_handling_without_silent_fail(self):
        original_stdin = sys.stdin
        sys.stdin = io.StringIO("")
        try:
            result = self.streamer.stream_and_persist(self.portfolio_id)
            self.assertFalse(result, "Пустой ввод должен корректно возвращать False без падений")
        finally:
            sys.stdin = original_stdin

if __name__ == '__main__':
    unittest.main()