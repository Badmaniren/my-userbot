import unittest
from unittest.mock import patch
import random
import uuid
import string
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)

class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.rand_storage = "".join(random.choices(string.ascii_letters, k=10))
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(db_storage=self.rand_storage)

    def test_init_and_dependencies(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        visualizer = MarketPortfolioStressAuditVisualizer(**{rand_key: rand_val})
        self.assertEqual(visualizer.dependencies.get(rand_key), rand_val)
        self.assertEqual(visualizer.db_storage, visualizer.dependencies.get("db_storage"))

    def test_visualize_method_delegation(self):
        rand_id = uuid.uuid4().hex
        payload = {"portfolio_id": rand_id, "format": "text_summary"}
        res_instance = self.visualizer_instance.visualize(payload)
        res_function = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(res_instance, res_function)
        self.assertIn(rand_id, res_instance)

    def test_payload_not_dict(self):
        rand_string = "".join(random.choices(string.ascii_letters, k=15))
        res = market_portfolio_stress_audit_visualizer(rand_string)
        self.assertEqual(res, rand_string)

        rand_number = random.randint(1000, 99999)
        res_num = market_portfolio_stress_audit_visualizer(rand_number)
        self.assertEqual(res_num, str(rand_number))

    def test_portfolio_id_vs_report_id(self):
        portfolio_id = uuid.uuid4().hex
        report_id = uuid.uuid4().hex

        payload_1 = {"portfolio_id": portfolio_id}
        res_1 = market_portfolio_stress_audit_visualizer(payload_1)
        self.assertIn(portfolio_id, res_1)

        payload_2 = {"report_id": report_id}
        res_2 = market_portfolio_stress_audit_visualizer(payload_2)
        self.assertIn(report_id, res_2)

    def test_text_summary_format_variations(self):
        rand_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(1.0, 100.0), 2)

        payload_basic = {"portfolio_id": rand_id, "format": "text_summary"}
        res_basic = market_portfolio_stress_audit_visualizer(payload_basic)
        self.assertIn(rand_id, res_basic)
        self.assertNotIn("Adaptive Risk Score", res_basic)
        self.assertNotIn("Exported to text report", res_basic)

        payload_with_score = {
            "portfolio_id": rand_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score
        }
        res_with_score = market_portfolio_stress_audit_visualizer(payload_with_score)
        self.assertIn(str(adaptive_score), res_with_score)

        payload_full = {
            "report_id": rand_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }
        res_full = market_portfolio_stress_audit_visualizer(payload_full)
        self.assertIn(rand_id, res_full)
        self.assertIn(str(adaptive_score), res_full)
        self.assertIn("Exported to text report successfully.", res_full)

    def test_graphical_format_variations(self):
        rand_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(0.1, 50.0), 4)
        rand_format = "".join(random.choices(string.ascii_lowercase, k=8))

        payload_graph = {"portfolio_id": rand_id, "format": rand_format}
        res_graph = market_portfolio_stress_audit_visualizer(payload_graph)

        self.assertEqual(res_graph.get("portfolio_id"), rand_id)
        self.assertEqual(res_graph.get("status"), "success")
        self.assertEqual(res_graph.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", res_graph)

        payload_graph_score = {
            "report_id": rand_id,
            "format": rand_format,
            "adaptive_risk_score": adaptive_score
        }
        res_graph_score = market_portfolio_stress_audit_visualizer(payload_graph_score)

        self.assertEqual(res_graph_score.get("portfolio_id"), rand_id)
        self.assertEqual(res_graph_score.get("adaptive_risk_score"), adaptive_score)
        self.assertEqual(res_graph_score.get("status"), "success")

    def test_external_dependencies_importability(self):
        rand_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        rand_bytes = bytes(uuid.uuid4().hex, 'utf-8')

        with patch("requests.get") as mock_get:
            mock_get.return_value.content = rand_bytes
            mock_get.return_value.status_code = 200
            
            response = requests.get(rand_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, rand_bytes)

        rand_html = f"<html><body><div>{uuid.uuid4().hex}</div></body></html>"
        soup = BeautifulSoup(rand_html, "html.parser")
        self.assertIsNotNone(soup.div)
        self.assertIn(rand_html, str(soup))

if __name__ == "__main__":
    unittest.main()