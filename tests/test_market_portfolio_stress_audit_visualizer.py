import unittest
from unittest.mock import MagicMock, patch
import random
import uuid
import io

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(db_storage=uuid.uuid4().hex)

    def test_non_dict_payload_returns_string(self):
        random_str = uuid.uuid4().hex
        result = market_portfolio_stress_audit_visualizer(random_str)
        self.assertEqual(result, random_str)

        random_int = random.randint(1000, 99999)
        result_int = market_portfolio_stress_audit_visualizer(random_int)
        self.assertEqual(result_int, str(random_int))

    def test_text_summary_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn("Portfolio Stress Audit Summary", result)

    def test_text_summary_format_with_report_id(self):
        report_id = uuid.uuid4().hex
        payload = {
            "report_id": report_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(report_id, result)

    def test_text_summary_format_with_adaptive_score(self):
        portfolio_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(1.0, 100.0), 2)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_score), result)
        self.assertIn("Adaptive Risk Score", result)

    def test_text_summary_format_with_export_text(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "export_to_text_report": True
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn("Exported to text report successfully", result)

    def test_graphical_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        format_type = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": format_type
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", result)
        self.assertNotIn("tail_risk_metrics", result)
        self.assertNotIn("stream_payload", result)

    def test_graphical_format_with_all_optional_fields(self):
        portfolio_id = uuid.uuid4().hex
        format_type = uuid.uuid4().hex
        adaptive_score = round(random.uniform(1.0, 50.0), 4)
        tail_risk_metrics = {uuid.uuid4().hex: random.random()}
        stream_payload = uuid.uuid4().hex

        payload = {
            "report_id": portfolio_id,
            "format": format_type,
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": tail_risk_metrics,
            "stream_payload": stream_payload
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("adaptive_risk_score"), adaptive_score)
        self.assertEqual(result.get("tail_risk_metrics"), tail_risk_metrics)
        self.assertEqual(result.get("stream_payload"), stream_payload)

    def test_class_wrapper_visualize_method(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary"
        }
        result = self.visualizer_instance.visualize(payload)
        self.assertIn(portfolio_id, result)

    def test_io_stream_processing_context(self):
        random_bytes = uuid.uuid4().bytes + bytes([random.randint(0, 255) for _ in range(16)])
        stream = io.BytesIO(random_bytes)
        read_data = stream.read()
        self.assertEqual(read_data, random_bytes)

    def test_requests_and_bs4_integration_mock(self):
        fake_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        fake_html = f"<html><body><div>{uuid.uuid4().hex}</div></body></html>"

        req_module = requests if requests is not None else MagicMock()
        bs4_class = BeautifulSoup if BeautifulSoup is not None else MagicMock()

        with patch.object(req_module, "get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = fake_html
            mock_response.status_code = 200

            resp = req_module.get(fake_url)
            if BeautifulSoup is not None:
                soup = bs4_class(resp.text, "html.parser")
                div_text = soup.find("div").text
                self.assertTrue(len(div_text) > 0)
            else:
                mock_soup = bs4_class(resp.text, "html.parser")
                mock_soup.find.return_value.text = fake_html
                div_text = mock_soup.find("div").text
                self.assertIn(fake_html, div_text)

            self.assertIn(fake_html, resp.text)