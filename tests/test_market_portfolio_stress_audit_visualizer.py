import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer

class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):
    def setUp(self):
        self.random_db = f"db_{uuid.uuid4().hex}"
        self.visualizer = MarketPortfolioStressAuditVisualizer(db_storage=self.random_db)

    def test_visualize_text_summary_format(self):
        portfolio_id = uuid.uuid4().hex
        adaptive_score = random.uniform(0, 100)
        
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }

        result = self.visualizer.visualize(payload)

        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_score), result)
        self.assertIn("Exported to text report successfully", result)
        self.assertTrue(result.startswith("Portfolio Stress Audit Summary"))

    def test_visualize_graphical_format(self):
        portfolio_id = uuid.uuid4().hex
        adaptive_score = random.random()
        tail_risk = {"var": random.random(), "cvar": random.random()}
        stream_payload = "".join(random.choices(string.ascii_letters, k=16))

        payload = {
            "portfolio_id": portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": tail_risk,
            "stream_payload": stream_payload
        }

        result = self.visualizer.visualize(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["adaptive_risk_score"], adaptive_score)
        self.assertEqual(result["tail_risk_metrics"], tail_risk)
        self.assertEqual(result["stream_payload"], stream_payload)

    def test_visualize_invalid_payload_type(self):
        random_str = uuid.uuid4().hex
        result = self.visualizer.visualize(random_str)
        self.assertEqual(result, random_str)

    def test_visualize_missing_optional_fields(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "report_id": portfolio_id,
            "format": "graphical"
        }

        result = self.visualizer.visualize(payload)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertNotIn("adaptive_risk_score", result)
        self.assertNotIn("tail_risk_metrics", result)

    def test_dependency_injection_integrity(self):
        mock_db = MagicMock()
        visualizer = MarketPortfolioStressAuditVisualizer(db_storage=mock_db)
        self.assertEqual(visualizer.db_storage, mock_db)

    def test_visualize_with_mocked_external_call(self):
        # Имитация проверки доступности через requests, если бы она была в модуле
        with patch('requests.get') as mock_get:
            random_url = f"https://{uuid.uuid4().hex}.audit.internal"
            mock_get.return_value.status_code = 200
            
            # Проверка, что визуализатор не падает при передаче сложных структур
            payload = {"portfolio_id": uuid.uuid4().hex, "format": "graphical"}
            result = self.visualizer.visualize(payload)
            
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["portfolio_id"], payload["portfolio_id"])

if __name__ == '__main__':
    unittest.main()