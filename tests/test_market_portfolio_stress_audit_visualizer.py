import unittest
from unittest.mock import patch
import random
import uuid
import string
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer,
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_db_value = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(db_storage=self.random_db_value)

    def test_init_and_dependencies(self):
        self.assertEqual(self.visualizer_instance.db_storage, self.random_db_value)
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        custom_instance = MarketPortfolioStressAuditVisualizer(**{random_key: random_val})
        self.assertEqual(custom_instance.dependencies.get(random_key), random_val)

    def test_visualize_method_delegation(self):
        portfolio_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(0.0, 100.0), 2)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score
        }
        result = self.visualizer_instance.visualize(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_score), result)

    def test_non_dict_payload(self):
        random_payload = uuid.uuid4().hex
        result = market_portfolio_stress_audit_visualizer(random_payload)
        self.assertEqual(result, str(random_payload))

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
        self.assertIn("Data successfully audited and visualized.", result)

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
        adaptive_score = round(random.uniform(1.0, 99.9), 4)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn(f"Adaptive Risk Score: {adaptive_score}.", result)

    def test_text_summary_format_with_export_text(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "export_to_text_report": True
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_default(self):
        portfolio_id = uuid.uuid4().hex
        format_type = "".join(random.choices(string.ascii_lowercase, k=8))
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

    def test_graphical_format_full_payload(self):
        portfolio_id = uuid.uuid4().hex
        format_type = "".join(random.choices(string.ascii_lowercase, k=10))
        adaptive_score = round(random.uniform(0.1, 50.0), 3)
        tail_metric_key = uuid.uuid4().hex
        tail_metric_val = random.randint(100, 999)
        tail_risk_metrics = {tail_metric_key: tail_metric_val}
        stream_key = uuid.uuid4().hex
        stream_val = uuid.uuid4().hex
        stream_payload = {stream_key: stream_val}

        payload = {
            "portfolio_id": portfolio_id,
            "format": format_type,
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": tail_risk_metrics,
            "stream_payload": stream_payload
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), adaptive_score)
        self.assertEqual(result.get("tail_risk_metrics"), tail_risk_metrics)
        self.assertEqual(result.get("stream_payload"), stream_payload)


if __name__ == "__main__":
    unittest.main()