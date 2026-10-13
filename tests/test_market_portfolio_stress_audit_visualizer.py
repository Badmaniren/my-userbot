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
        self.rand_str = lambda: "".join(random.choices(string.ascii_letters, k=10))
        self.portfolio_id = uuid.uuid4().hex
        self.db_mock = {self.rand_str(): random.randint(100, 999)}
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(
            db_storage=self.db_mock,
            extractor_tool_1790087207=self.rand_str()
        )

    def test_init_and_dependencies(self):
        self.assertEqual(self.visualizer_instance.db_storage, self.db_mock)
        self.assertIn("db_storage", self.visualizer_instance.dependencies)
        self.assertIn("extractor_tool_1790087207", self.visualizer_instance.dependencies)

    def test_visualizer_method_delegation(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": round(random.uniform(1.0, 99.9), 2)
        }
        res_direct = market_portfolio_stress_audit_visualizer(payload)
        res_class = self.visualizer_instance.visualize(payload)
        self.assertEqual(res_direct, res_class)
        self.assertIn(self.portfolio_id, res_class)

    def test_non_dict_payload(self):
        random_number = random.randint(1000, 9999)
        payload = f"{self.rand_str()}_{random_number}"
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(res, str(payload))

    def test_text_summary_format_basic(self):
        payload = {
            "report_id": self.portfolio_id,
            "format": "text_summary"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(self.portfolio_id, res)
        self.assertIn("Portfolio Stress Audit Summary", res)
        self.assertIn("Data successfully audited and visualized.", res)

    def test_text_summary_format_with_score_and_export(self):
        score = round(random.uniform(0.01, 10.0), 4)
        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": score,
            "export_to_text_report": True
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(self.portfolio_id, res)
        self.assertIn(f"Adaptive Risk Score: {score}", res)
        self.assertIn("Exported to text report successfully.", res)

    def test_graphical_format_basic(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "graphical"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["layout"], "graphical")
        self.assertNotIn("adaptive_risk_score", res)
        self.assertNotIn("tail_risk_metrics", res)

    def test_graphical_format_extended_fields(self):
        score = round(random.uniform(10.0, 50.0), 2)
        tail_metric_key = self.rand_str()
        tail_metric_val = random.random()
        tail_metrics = {tail_metric_key: tail_metric_val}
        stream_key = self.rand_str()
        stream_val = self.rand_str()
        stream_payload = {stream_key: stream_val}

        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": score,
            "tail_risk_metrics": tail_metrics,
            "stream_payload": stream_payload
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["layout"], "graphical")
        self.assertEqual(res["adaptive_risk_score"], score)
        self.assertEqual(res["tail_risk_metrics"], tail_metrics)
        self.assertEqual(res["stream_payload"], stream_payload)


if __name__ == "__main__":
    unittest.main()