import unittest
from unittest.mock import patch, MagicMock
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
        self.random_deps = {
            "db_storage": uuid.uuid4().hex,
            "market_portfolio_stress_audit_visualizer": uuid.uuid4().hex,
            "market_portfolio_collector_agent": uuid.uuid4().hex
        }
        self.visualizer = MarketPortfolioStressAuditVisualizer(**self.random_deps)

    def test_init_and_dependencies(self):
        self.assertEqual(self.visualizer.dependencies, self.random_deps)
        self.assertEqual(self.visualizer.db_storage, self.random_deps["db_storage"])

    def test_visualize_proxy_call(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_score = round(random.uniform(1.0, 100.0), 2)
        payload = {
            "portfolio_id": rand_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": rand_score
        }
        
        result_direct = market_portfolio_stress_audit_visualizer(payload)
        result_proxy = self.visualizer.visualize(payload)
        
        self.assertEqual(result_direct, result_proxy)
        self.assertIn(rand_portfolio_id, result_proxy)
        self.assertIn(str(rand_score), result_proxy)

    def test_payload_not_dict(self):
        rand_string = ''.join(random.choices(string.ascii_letters, k=15))
        result = market_portfolio_stress_audit_visualizer(rand_string)
        self.assertEqual(result, rand_string)

    def test_text_summary_format(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_score = random.randint(10, 999)
        payload = {
            "report_id": rand_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": rand_score,
            "export_to_text_report": True
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(rand_portfolio_id, result)
        self.assertIn(str(rand_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_full_payload(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_score = round(random.uniform(0.01, 99.99), 4)
        rand_tail_risk = {uuid.uuid4().hex: random.random() for _ in range(3)}
        rand_stream = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(2)}
        
        payload = {
            "portfolio_id": rand_portfolio_id,
            "format": uuid.uuid4().hex,
            "adaptive_risk_score": rand_score,
            "tail_risk_metrics": rand_tail_risk,
            "stream_payload": rand_stream
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["layout"], "graphical")
        self.assertEqual(result["adaptive_risk_score"], rand_score)
        self.assertEqual(result["tail_risk_metrics"], rand_tail_risk)
        self.assertEqual(result["stream_payload"], rand_stream)

    def test_graphical_format_minimal_payload(self):
        rand_report_id = uuid.uuid4().hex
        payload = {
            "report_id": rand_report_id,
            "format": "graphical"
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], rand_report_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["layout"], "graphical")
        self.assertNotIn("adaptive_risk_score", result)
        self.assertNotIn("tail_risk_metrics", result)
        self.assertNotIn("stream_payload", result)

    def test_network_and_parsing_behavior_simulation(self):
        rand_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        rand_html_content = f"<html><body><div id='{uuid.uuid4().hex}'>{uuid.uuid4().hex}</div></body></html>".encode('utf-8')
        
        mock_response = MagicMock()
        mock_response.content = rand_html_content
        mock_response.status_code = 200

        with patch("requests.get", return_value=mock_response) as mock_get:
            response = requests.get(rand_url)
            mock_get.assert_called_once_with(rand_url)
            
            stream_data = io.BytesIO(response.content)
            soup = BeautifulSoup(stream_data.read(), 'html.parser')
            
            extracted_text = soup.get_text()
            self.assertIsNotNone(extracted_text)
            self.assertTrue(len(extracted_text) > 0)


if __name__ == "__main__":
    unittest.main()