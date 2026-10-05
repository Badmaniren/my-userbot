import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.rand_storage = "".join(random.choices(string.ascii_letters, k=10))
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(db_storage=self.rand_storage)

    def test_init_and_dependencies(self):
        self.assertEqual(self.visualizer_instance.db_storage, self.rand_storage)
        
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        custom_instance = MarketPortfolioStressAuditVisualizer(**{random_key: random_val})
        self.assertEqual(custom_instance.dependencies.get(random_key), random_val)

    def test_non_dict_payload(self):
        random_string_payload = uuid.uuid4().hex
        result = market_portfolio_stress_audit_visualizer(random_string_payload)
        self.assertEqual(result, random_string_payload)

        random_int_payload = random.randint(1000, 99999)
        result_int = market_portfolio_stress_audit_visualizer(random_int_payload)
        self.assertEqual(result_int, str(random_int_payload))

    def test_text_summary_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary"
        }
        
        result = self.visualizer_instance.visualize(payload)
        expected_msg = (
            f"Portfolio Stress Audit Summary for {portfolio_id}: "
            f"Data successfully audited and visualized."
        )
        self.assertEqual(result, expected_msg)

    def test_text_summary_format_with_adaptive_score(self):
        report_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(1.0, 100.0), 2)
        payload = {
            "report_id": report_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIn(report_id, result)
        self.assertIn(str(adaptive_score), result)
        self.assertIn("Adaptive Risk Score:", result)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        random_format = "".join(random.choices(string.ascii_lowercase, k=8))
        
        payload = {
            "portfolio_id": portfolio_id,
            "format": random_format
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", result)
        self.assertNotIn("tail_risk_metrics", result)
        self.assertNotIn("stream_payload", result)

    def test_graphical_format_extended_metrics(self):
        portfolio_id = uuid.uuid4().hex
        adaptive_score = random.randint(50, 500)
        tail_risk_metric_key = uuid.uuid4().hex
        tail_risk_metric_val = random.random()
        tail_risk_metrics = {tail_risk_metric_key: tail_risk_metric_val}
        stream_payload = {"stream_id": uuid.uuid4().hex}

        payload = {
            "portfolio_id": portfolio_id,
            "format": uuid.uuid4().hex,
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": tail_risk_metrics,
            "stream_payload": stream_payload
        }

        result = self.visualizer_instance.visualize(payload)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["adaptive_risk_score"], adaptive_score)
        self.assertEqual(result["tail_risk_metrics"], tail_risk_metrics)
        self.assertEqual(result["stream_payload"], stream_payload)


if __name__ == "__main__":
    unittest.main()