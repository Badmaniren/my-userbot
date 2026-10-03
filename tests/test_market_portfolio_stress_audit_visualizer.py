import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.visualizer = MarketPortfolioStressAuditVisualizer()
        self.random_portfolio_id = uuid.uuid4().hex
        self.random_score = round(random.uniform(1.0, 100.0), 2)
        self.random_tail_risk = {uuid.uuid4().hex: random.random()}
        self.random_stream = uuid.uuid4().hex

    def test_visualize_non_dict_payload(self):
        random_string = ''.join(random.choices(string.ascii_letters, k=10))
        result = self.visualizer.visualize(random_string)
        self.assertEqual(result, str(random_string))

    def test_market_portfolio_stress_audit_visualizer_text_summary(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.random_score,
            "export_to_text_report": True
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(self.random_portfolio_id, result)
        self.assertIn(str(self.random_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_market_portfolio_stress_audit_visualizer_graphical(self):
        payload = {
            "report_id": self.random_portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.random_score,
            "tail_risk_metrics": self.random_tail_risk,
            "stream_payload": self.random_stream
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(result["portfolio_id"], self.random_portfolio_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["layout"], "graphical")
        self.assertEqual(result["adaptive_risk_score"], self.random_score)
        self.assertEqual(result["tail_risk_metrics"], self.random_tail_risk)
        self.assertEqual(result["stream_payload"], self.random_stream)

    def test_network_and_io_context_resilience(self):
        random_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        random_html_content = f"<html><body><span>{uuid.uuid4().hex}</span></body></html>"

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = random_html_content.encode('utf-8')
            mock_response.text = random_html_content
            mock_get.return_value = mock_response

            response = requests.get(random_url)
            self.assertEqual(response.status_code, 200)

            soup = BeautifulSoup(response.text, 'html.parser')
            span_text = soup.find('span').text
            self.assertEqual(span_text, random_html_content.split('<span>')[1].split('</span>')[0])

        io_stream = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        read_data = io_stream.read().decode('utf-8')
        self.assertTrue(len(read_data) > 0)


if __name__ == "__main__":
    unittest.main()