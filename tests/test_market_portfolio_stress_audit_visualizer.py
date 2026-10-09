import unittest
from unittest.mock import patch
import uuid
import random
import string
import requests
from bs4 import BeautifulSoup
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer,
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_portfolio_id = uuid.uuid4().hex
        self.random_score = round(random.uniform(1.0, 100.0), 2)
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(
            db_storage=uuid.uuid4().hex
        )

    def test_non_dict_payload(self):
        random_str_payload = "".join(random.choices(string.ascii_letters, k=15))
        result = market_portfolio_stress_audit_visualizer(random_str_payload)
        self.assertEqual(result, random_str_payload)

    def test_text_summary_format_basic(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "text_summary",
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(self.random_portfolio_id, result)
        self.assertIn("Portfolio Stress Audit Summary", result)
        self.assertIn("Data successfully audited and visualized.", result)

    def test_text_summary_format_with_adaptive_score(self):
        payload = {
            "report_id": self.random_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.random_score,
            "export_to_text_report": True,
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(self.random_portfolio_id, result)
        self.assertIn(f"Adaptive Risk Score: {self.random_score}.", result)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_default(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "graphical",
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.random_portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", result)

    def test_graphical_format_extended(self):
        tail_metrics = {"var_95": random.random(), "cvar_99": random.random()}
        stream_data = {"stream_id": uuid.uuid4().hex, "active": True}
        
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "graphical_custom",
            "adaptive_risk_score": self.random_score,
            "tail_risk_metrics": tail_metrics,
            "stream_payload": stream_data,
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.random_portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.random_score)
        self.assertEqual(result.get("tail_risk_metrics"), tail_metrics)
        self.assertEqual(result.get("stream_payload"), stream_data)

    def test_class_wrapper_delegation(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.random_score,
        }
        result = self.visualizer_instance.visualize(payload)
        self.assertIn(self.random_portfolio_id, result)
        self.assertIn(str(self.random_score), result)

    def test_network_and_parser_mocking_integration(self):
        random_url = f"https://{uuid.uuid4().hex}.com/audit"
        random_html_content = f"<html><body><div id='portfolio'>{self.random_portfolio_id}</div></body></html>"
        
        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.status_code = 200
            mock_response.text = random_html_content
            
            response = requests.get(random_url)
            soup = BeautifulSoup(response.text, "html.parser")
            extracted_id = soup.find("div", {"id": "portfolio"}).text
            
            self.assertEqual(extracted_id, self.random_portfolio_id)
            mock_get.assert_called_once_with(random_url)