import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer, market_portfolio_stress_audit_visualizer

class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_id = uuid.uuid4().hex
        self.random_score = random.uniform(0, 100)
        self.random_metrics = {uuid.uuid4().hex: random.random() for _ in range(3)}
        self.random_stream = uuid.uuid4().hex
        self.visualizer = MarketPortfolioStressAuditVisualizer(db_storage=MagicMock())

    def test_visualize_text_summary_logic(self):
        payload = {
            "portfolio_id": self.random_id,
            "format": "text_summary",
            "adaptive_risk_score": self.random_score,
            "export_to_text_report": True
        }

        result = self.visualizer.visualize(payload)

        self.assertIn(self.random_id, result)
        self.assertIn(str(self.random_score), result)
        self.assertIn("Exported to text report successfully", result)

    def test_visualize_graphical_format_logic(self):
        payload = {
            "portfolio_id": self.random_id,
            "format": "graphical",
            "adaptive_risk_score": self.random_score,
            "tail_risk_metrics": self.random_metrics,
            "stream_payload": self.random_stream
        }

        result = market_portfolio_stress_audit_visualizer(payload)

        self.assertEqual(result["portfolio_id"], self.random_id)
        self.assertEqual(result["adaptive_risk_score"], self.random_score)
        self.assertEqual(result["tail_risk_metrics"], self.random_metrics)
        self.assertEqual(result["stream_payload"], self.random_stream)
        self.assertEqual(result["layout"], "graphical")

    def test_invalid_payload_handling(self):
        random_string = ''.join(random.choices(string.ascii_letters, k=10))
        result = market_portfolio_stress_audit_visualizer(random_string)
        self.assertEqual(result, random_string)

    def test_fallback_id_logic(self):
        report_id = uuid.uuid4().hex
        payload = {
            "report_id": report_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(report_id, result)

    def test_integration_with_exporter_mock(self):
        # Проверка изоляции через мок, чтобы избежать ImportError при отсутствии модуля
        with patch('skills.market_portfolio_stress_audit_visualizer.market_portfolio_stress_audit_exporter_v2', create=True) as mock_exporter:
            mock_exporter.return_value = True
            payload = {"portfolio_id": self.random_id}

            # Если бы визуализатор вызывал экспортер напрямую, мы бы проверяли вызов здесь
            # В текущей архитектуре проверяем корректность обработки данных
            result = self.visualizer.visualize(payload)
            self.assertIsInstance(result, str)

if __name__ == '__main__':
    unittest.main()