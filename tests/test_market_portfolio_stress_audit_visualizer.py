import unittest
from unittest.mock import patch
import uuid
import random
import string
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer,
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):
    def setUp(self):
        self.rand_storage_key = uuid.uuid4().hex
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(
            db_storage=self.rand_storage_key
        )

    def test_class_initialization_and_delegate(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_score = round(random.uniform(1.0, 100.0), 2)
        payload = {
            "portfolio_id": rand_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": rand_score,
            "export_to_text_report": True,
        }
        res_method = self.visualizer_instance.visualize(payload)
        res_function = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(res_method, res_function)
        self.assertIn(rand_portfolio_id, res_method)
        self.assertIn(str(rand_score), res_method)

    def test_non_dict_payload_returns_string(self):
        rand_suffix = "".join(random.choices(string.ascii_letters, k=10))
        random_int = random.randint(1000, 99999)
        payload = f"{rand_suffix}_{random_int}"
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(result, payload)

    def test_text_summary_format_basic(self):
        rand_report_id = uuid.uuid4().hex
        payload = {
            "report_id": rand_report_id,
            "format": "text_summary",
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_report_id, result)
        self.assertIn("Portfolio Stress Audit Summary", result)
        self.assertNotIn("Adaptive Risk Score", result)
        self.assertNotIn("Exported to text report", result)

    def test_text_summary_format_with_adaptive_score(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_score = random.randint(50, 500)
        payload = {
            "portfolio_id": rand_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": rand_score,
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_portfolio_id, result)
        self.assertIn(f"Adaptive Risk Score: {rand_score}", result)

    def test_text_summary_format_with_export_flag(self):
        rand_portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": rand_portfolio_id,
            "format": "text_summary",
            "export_to_text_report": True,
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_portfolio_id, result)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_basic(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_format = uuid.uuid4().hex
        payload = {
            "portfolio_id": rand_portfolio_id,
            "format": rand_format,
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), rand_portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", result)
        self.assertNotIn("tail_risk_metrics", result)
        self.assertNotIn("stream_payload", result)

    def test_graphical_format_full_payload(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_format = uuid.uuid4().hex
        rand_score = random.random()
        rand_tail_risk = {uuid.uuid4().hex: random.random()}
        rand_stream = uuid.uuid4().hex

        payload = {
            "portfolio_id": rand_portfolio_id,
            "format": rand_format,
            "adaptive_risk_score": rand_score,
            "tail_risk_metrics": rand_tail_risk,
            "stream_payload": rand_stream,
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), rand_portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), rand_score)
        self.assertEqual(result.get("tail_risk_metrics"), rand_tail_risk)
        self.assertEqual(result.get("stream_payload"), rand_stream)


if __name__ == "__main__":
    unittest.main()