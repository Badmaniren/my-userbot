import unittest
from unittest.mock import patch
import random
import uuid
import string
import io
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)

class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):
    def setUp(self):
        self.rand_str = lambda: uuid.uuid4().hex
        self.rand_int = lambda: random.randint(1000, 999999)
        self.rand_float = lambda: round(random.uniform(0.01, 999.99), 4)
        
        self.mock_db = self.rand_str()
        self.visualizer = MarketPortfolioStressAuditVisualizer(db_storage=self.mock_db)

    def test_initialization(self):
        self.assertEqual(self.visualizer.db_storage, self.mock_db)
        self.assertIn("db_storage", self.visualizer.dependencies)

    def test_visualize_wrapper_delegation(self):
        portfolio_id = self.rand_str()
        payload = {"portfolio_id": portfolio_id, "format": "text_summary"}
        
        result = self.visualizer.visualize(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn("Portfolio Stress Audit Summary", result)

    def test_non_dict_payload(self):
        random_payload_str = self.rand_str()
        result = market_portfolio_stress_audit_visualizer(random_payload_str)
        self.assertEqual(result, random_payload_str)

        random_payload_int = self.rand_int()
        result_int = market_portfolio_stress_audit_visualizer(random_payload_int)
        self.assertEqual(result_int, str(random_payload_int))

    def test_text_summary_format_basic(self):
        portfolio_id = self.rand_str()
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, res)
        self.assertIn("Data successfully audited and visualized", res)

    def test_text_summary_format_with_report_id(self):
        report_id = self.rand_str()
        payload = {
            "report_id": report_id,
            "format": "text_summary"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(report_id, res)

    def test_text_summary_with_adaptive_score(self):
        portfolio_id = self.rand_str()
        score = self.rand_float()
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": score
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, res)
        self.assertIn(f"Adaptive Risk Score: {score}", res)

    def test_text_summary_with_export(self):
        portfolio_id = self.rand_str()
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "export_to_text_report": True
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, res)
        self.assertIn("Exported to text report successfully", res)

    def test_text_summary_full_payload(self):
        portfolio_id = self.rand_str()
        score = self.rand_float()
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": score,
            "export_to_text_report": True
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, res)
        self.assertIn(str(score), res)
        self.assertIn("Exported to text report successfully", res)

    def test_graphical_format_basic(self):
        portfolio_id = self.rand_str()
        format_type = self.rand_str()
        payload = {
            "portfolio_id": portfolio_id,
            "format": format_type
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), portfolio_id)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", res)

    def test_graphical_format_with_adaptive_score(self):
        portfolio_id = self.rand_str()
        score = self.rand_float()
        format_type = self.rand_str()
        payload = {
            "report_id": portfolio_id,
            "format": format_type,
            "adaptive_risk_score": score
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), portfolio_id)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("layout"), "graphical")
        self.assertEqual(res.get("adaptive_risk_score"), score)

    def test_external_library_integration_mocking(self):
        random_url = f"https://{self.rand_str()}.com/{self.rand_str()}"
        random_html = f"<html><body><div id='{self.rand_str()}'>{self.rand_str()}</div></body></html>"
        
        with patch('requests.get') as mock_get:
            mock_response = mock_get.return_value
            mock_response.status_code = 200
            mock_response.content = random_html.encode('utf-8')
            
            resp = requests.get(random_url)
            soup = BeautifulSoup(io.BytesIO(resp.content), 'html.parser')
            
            self.assertEqual(resp.status_code, 200)
            self.assertIsNotNone(soup.find('div'))

if __name__ == '__main__':
    unittest.main()