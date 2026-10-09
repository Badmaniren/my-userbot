import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_portfolio_id = f"PORT-{uuid.uuid4().hex[:8].upper()}"
        self.random_report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"
        self.random_risk_score = round(random.uniform(1.0, 99.9), 2)
        self.random_tail_metric = f"TAIL-{uuid.uuid4().hex[:6]}"
        self.random_stream_data = f"STREAM-{uuid.uuid4().hex[:6]}"

        self.db_mock = MagicMock()
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(
            db_storage=self.db_mock,
            market_portfolio_stress_audit_visualizer=uuid.uuid4().hex
        )

    def test_non_dict_payload_returns_string(self):
        random_suffix = ''.join(random.choices(string.ascii_letters, k=10))
        payload = f"invalid_payload_{random_suffix}"
        
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, str)
        self.assertEqual(result, payload)

    def test_text_summary_format_basic(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "text_summary"
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(self.random_portfolio_id, result)
        self.assertIn("Portfolio Stress Audit Summary", result)
        self.assertIn("Data successfully audited and visualized.", result)

    def test_text_summary_format_with_adaptive_score(self):
        payload = {
            "report_id": self.random_report_id,
            "format": "text_summary",
            "adaptive_risk_score": self.random_risk_score
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(self.random_report_id, result)
        self.assertIn(str(self.random_risk_score), result)
        self.assertIn("Adaptive Risk Score:", result)

    def test_text_summary_format_with_export_flag(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "text_summary",
            "export_to_text_report": True
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(self.random_portfolio_id, result)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_basic(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "graphical"
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.random_portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", result)

    def test_graphical_format_full_payload(self):
        payload = {
            "report_id": self.random_report_id,
            "format": "graphical",
            "adaptive_risk_score": self.random_risk_score,
            "tail_risk_metrics": self.random_tail_metric,
            "stream_payload": self.random_stream_data
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.random_report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.random_risk_score)
        self.assertEqual(result.get("tail_risk_metrics"), self.random_tail_metric)
        self.assertEqual(result.get("stream_payload"), self.random_stream_data)

    def test_class_visualize_proxy_method(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.random_risk_score
        }
        
        result = self.visualizer_instance.visualize(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(self.random_portfolio_id, result)
        self.assertIn(str(self.random_risk_score), result)

    def test_class_initialization_with_dependencies(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        
        visualizer = MarketPortfolioStressAuditVisualizer(**{random_key: random_val})
        
        self.assertEqual(visualizer.dependencies.get(random_key), random_val)

    def test_io_stream_handling_simulation(self):
        random_bytes = uuid.uuid4().bytes
        stream_io = io.BytesIO(random_bytes)
        
        read_data = stream_io.read()
        self.assertEqual(read_data, random_bytes)

    def test_network_and_parser_mocking_integration(self):
        random_url = f"https://{uuid.uuid4().hex}.org/audit"
        random_html_snippet = f"<div>{uuid.uuid4().hex}</div>"

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.text = random_html_snippet
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            response = requests.get(random_url)
            soup = BeautifulSoup(response.text, "html.parser")
            extracted_text = soup.div.text

            mock_get.assert_called_once_with(random_url)
            self.assertEqual(extracted_text, random_html_snippet[5:-6])