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
            "db_storage": f"db_{uuid.uuid4().hex[:8]}",
            "market_portfolio_scenario_simulator": f"simulator_{uuid.uuid4().hex[:8]}"
        }
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(**self.random_deps)

    def test_init_stores_dependencies(self):
        self.assertEqual(self.visualizer_instance.db_storage, self.random_deps["db_storage"])
        self.assertEqual(self.visualizer_instance.dependencies, self.random_deps)

    def test_visualize_method_delegates_correctly(self):
        rand_portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": rand_portfolio_id,
            "format": "text_summary"
        }
        res = self.visualizer_instance.visualize(payload)
        self.assertIn(rand_portfolio_id, res)

    def test_non_dict_payload_returns_string(self):
        rand_string = ''.join(random.choices(string.ascii_letters, k=16))
        result = market_portfolio_stress_audit_visualizer(rand_string)
        self.assertEqual(result, rand_string)

        rand_number = random.randint(1000, 99999)
        result_num = market_portfolio_stress_audit_visualizer(rand_number)
        self.assertEqual(result_num, str(rand_number))

    def test_text_summary_format_basic(self):
        rand_id = f"port_{uuid.uuid4().hex[:6]}"
        payload = {
            "portfolio_id": rand_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_id, result)
        self.assertIn("Portfolio Stress Audit Summary", result)

    def test_text_summary_format_with_report_id_fallback(self):
        rand_report_id = f"rep_{uuid.uuid4().hex[:6]}"
        payload = {
            "report_id": rand_report_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_report_id, result)

    def test_text_summary_format_with_adaptive_score_and_export(self):
        rand_id = uuid.uuid4().hex[:8]
        rand_score = round(random.uniform(0.1, 99.9), 2)
        payload = {
            "portfolio_id": rand_id,
            "format": "text_summary",
            "adaptive_risk_score": rand_score,
            "export_to_text_report": True
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_id, result)
        self.assertIn(str(rand_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_basic(self):
        rand_id = uuid.uuid4().hex[:10]
        payload = {
            "portfolio_id": rand_id,
            "format": "graphical"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), rand_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")

    def test_graphical_format_extended_fields(self):
        rand_id = uuid.uuid4().hex[:10]
        rand_score = round(random.uniform(1.0, 10.0), 4)
        rand_tail_risk = {uuid.uuid4().hex[:4]: random.random()}
        rand_stream = {uuid.uuid4().hex[:4]: uuid.uuid4().hex}

        payload = {
            "report_id": rand_id,
            "format": "graphical",
            "adaptive_risk_score": rand_score,
            "tail_risk_metrics": rand_tail_risk,
            "stream_payload": rand_stream
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(result.get("portfolio_id"), rand_id)
        self.assertEqual(result.get("adaptive_risk_score"), rand_score)
        self.assertEqual(result.get("tail_risk_metrics"), rand_tail_risk)
        self.assertEqual(result.get("stream_payload"), rand_stream)

    def test_requests_and_bs4_integration_mock(self):
        rand_url = f"https://{uuid.uuid4().hex[:8]}.com/audit"
        rand_html_text = f"<html><body><div id='{uuid.uuid4().hex[:6]}'>Stress Audit Data</div></body></html>"

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = rand_html_text
            mock_response.content = rand_html_text.encode('utf-8')
            mock_get.return_value = mock_response

            resp = requests.get(rand_url)
            soup = BeautifulSoup(resp.text, "html.parser")
            
            self.assertEqual(resp.status_code, 200)
            self.assertIsNotNone(soup.body)

    def test_io_bytes_stream_processing(self):
        rand_bytes = f"audit_dump_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(rand_bytes)
        
        read_data = stream.read()
        self.assertEqual(read_data, rand_bytes)


if __name__ == "__main__":
    unittest.main()