import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)

class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):
    def setUp(self):
        self.rand_str = lambda: ''.join(random.choices(string.ascii_letters, k=10))
        self.portfolio_id = uuid.uuid4().hex
        self.report_id = uuid.uuid4().hex
        self.mock_db = MagicMock()
        self.visualizer = MarketPortfolioStressAuditVisualizer(db_storage=self.mock_db)

    def test_visualizer_class_init_and_call(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "text_summary"
        }
        res = self.visualizer.visualize(payload)
        self.assertIn(self.portfolio_id, res)
        self.assertIsInstance(res, str)

    def test_market_portfolio_stress_audit_visualizer_invalid_payload(self):
        random_payload = random.randint(1000, 99999)
        res = market_portfolio_stress_audit_visualizer(random_payload)
        self.assertEqual(res, str(random_payload))

    def test_market_portfolio_stress_audit_visualizer_text_summary(self):
        payload = {
            "report_id": self.report_id,
            "format": "text_summary"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(self.report_id, res)
        self.assertTrue(res.startswith("Portfolio Stress Audit Summary"))

    def test_market_portfolio_stress_audit_visualizer_graphical_format(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "format": self.rand_str()
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("layout"), "graphical")

    def test_visualizer_with_storage_dependency(self):
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = f"<html><body>{self.rand_str()}</body></html>"
            mock_get.return_value = mock_resp

            payload = {
                "portfolio_id": self.portfolio_id,
                "format": "text_summary"
            }
            res = self.visualizer.visualize(payload)
            self.assertIn(self.portfolio_id, res)

if __name__ == '__main__':
    unittest.main()