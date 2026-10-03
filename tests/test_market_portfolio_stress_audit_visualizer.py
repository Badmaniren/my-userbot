import unittest
from unittest.mock import patch
import random
import uuid
import string
import io

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_deps = {
            "db_storage": uuid.uuid4().hex,
            f"extractor_tool_{random.randint(100000000, 999999999)}": uuid.uuid4().hex,
            "market_parser": "".join(random.choices(string.ascii_letters, k=10))
        }
        self.visualizer = MarketPortfolioStressAuditVisualizer(**self.random_deps)

    def test_non_dict_payload_handling(self):
        random_string = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        result = self.visualizer.visualize(random_string)
        self.assertEqual(result, random_string)

    def test_text_summary_format_generation(self):
        portfolio_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(1.0, 100.0), 2)
        
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }

        result = self.visualizer.visualize(payload)
        
        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_generation(self):
        report_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(-50.0, 50.0), 4)
        tail_risk = "".join(random.choices(string.ascii_lowercase, k=8))
        stream_data = "".join(random.choices(string.digits, k=6))

        payload = {
            "report_id": report_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": tail_risk,
            "stream_payload": stream_data
        }

        result = market_portfolio_stress_audit_visualizer(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), adaptive_score)
        self.assertEqual(result.get("tail_risk_metrics"), tail_risk)
        self.assertEqual(result.get("stream_payload"), stream_data)

    def test_stream_payload_io_mocking(self):
        random_bytes = uuid.uuid4().bytes
        stream_io = io.BytesIO(random_bytes)
        
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "graphical",
            "stream_payload": stream_io.read()
        }

        result = self.visualizer.visualize(payload)
        self.assertEqual(result.get("stream_payload"), random_bytes)


if __name__ == "__main__":
    unittest.main()