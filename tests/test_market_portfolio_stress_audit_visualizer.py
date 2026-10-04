import unittest
from unittest.mock import patch
import random
import uuid
import string
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):
    def setUp(self):
        self.random_deps = {
            "db_storage": uuid.uuid4().hex,
            "market_portfolio_alert_dispatcher": uuid.uuid4().hex,
            "market_report_generator": uuid.uuid4().hex
        }
        self.visualizer = MarketPortfolioStressAuditVisualizer(**self.random_deps)

    def test_init_and_dependencies(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        instance = MarketPortfolioStressAuditVisualizer(**{rand_key: rand_val})
        self.assertEqual(instance.db_storage, instance.dependencies.get("db_storage"))
        self.assertEqual(instance.dependencies[rand_key], rand_val)

    def test_visualizer_invalid_payload_returns_string(self):
        rand_int = random.randint(1000, 99999)
        result = self.visualizer.visualize(rand_int)
        self.assertEqual(result, str(rand_int))

    def test_text_summary_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary"
        }
        res_class = self.visualizer.visualize(payload)
        res_func = market_portfolio_stress_audit_visualizer(payload)

        expected = (
            f"Portfolio Stress Audit Summary for {portfolio_id}: "
            f"Data successfully audited and visualized."
        )
        self.assertEqual(res_class, expected)
        self.assertEqual(res_func, expected)

    def test_text_summary_format_with_adaptive_score(self):
        report_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(1.0, 100.0), 2)
        payload = {
            "report_id": report_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }
        result = self.visualizer.visualize(payload)

        self.assertIn(report_id, result)
        self.assertIn(str(adaptive_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_default(self):
        portfolio_id = ''.join(random.choices(string.ascii_letters, k=10))
        format_type = ''.join(random.choices(string.ascii_lowercase, k=8))
        payload = {
            "portfolio_id": portfolio_id,
            "format": format_type
        }
        result = self.visualizer.visualize(payload)

        expected = {
            "portfolio_id": portfolio_id,
            "status": "success",
            "layout": "graphical",
        }
        self.assertEqual(result, expected)

    def test_graphical_format_extended_fields(self):
        portfolio_id = uuid.uuid4().hex
        adaptive_score = random.randint(1, 500)
        tail_risk_metrics = {
            uuid.uuid4().hex: random.random(),
            uuid.uuid4().hex: random.random()
        }
        stream_payload = {
            uuid.uuid4().hex: uuid.uuid4().hex
        }

        payload = {
            "portfolio_id": portfolio_id,
            "format": uuid.uuid4().hex,
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": tail_risk_metrics,
            "stream_payload": stream_payload
        }

        result = self.visualizer.visualize(payload)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["layout"], "graphical")
        self.assertEqual(result["adaptive_risk_score"], adaptive_score)
        self.assertEqual(result["tail_risk_metrics"], tail_risk_metrics)
        self.assertEqual(result["stream_payload"], stream_payload)


if __name__ == "__main__":
    unittest.main()