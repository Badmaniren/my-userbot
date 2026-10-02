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
        self.random_deps = {
            "".join(random.choices(string.ascii_lowercase, k=8)): uuid.uuid4().hex
            for _ in range(3)
        }
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(**self.random_deps)

    def test_init_stores_dependencies(self):
        self.assertEqual(self.visualizer_instance.dependencies, self.random_deps)
        db_key = "".join(random.choices(string.ascii_lowercase, k=6))
        db_val = uuid.uuid4().hex
        custom_inst = MarketPortfolioStressAuditVisualizer(db_storage={db_key: db_val})
        self.assertEqual(custom_inst.db_storage, {db_key: db_val})

    def test_visualize_proxy_method(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_score = round(random.uniform(1.0, 100.0), 2)
        payload = {
            "portfolio_id": rand_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": rand_score,
        }
        res_direct = market_portfolio_stress_audit_visualizer(payload)
        res_proxy = self.visualizer_instance.visualize(payload)
        self.assertEqual(res_direct, res_proxy)

    def test_non_dict_payload_returns_string(self):
        rand_int = random.randint(-10000, 10000)
        res = market_portfolio_stress_audit_visualizer(rand_int)
        self.assertEqual(res, str(rand_int))

        rand_str = uuid.uuid4().hex
        res_str = market_portfolio_stress_audit_visualizer(rand_str)
        self.assertEqual(res_str, rand_str)

    def test_text_summary_format_basic(self):
        rand_id = uuid.uuid4().hex
        payload = {
            "report_id": rand_id,
            "format": "text_summary",
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_id, res)
        self.assertIn("Portfolio Stress Audit Summary", res)
        self.assertIn("Data successfully audited and visualized.", res)

    def test_text_summary_with_adaptive_score_and_export(self):
        rand_id = uuid.uuid4().hex
        rand_score = round(random.uniform(0.1, 999.9), 4)
        payload = {
            "portfolio_id": rand_id,
            "format": "text_summary",
            "adaptive_risk_score": rand_score,
            "export_to_text_report": True,
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_id, res)
        self.assertIn(str(rand_score), res)
        self.assertIn("Adaptive Risk Score:", res)
        self.assertIn("Exported to text report successfully.", res)

    def test_graphical_format_basic(self):
        rand_id = uuid.uuid4().hex
        rand_format = "".join(random.choices(string.ascii_lowercase, k=5)) + "_graph"
        payload = {
            "portfolio_id": rand_id,
            "format": rand_format,
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), rand_id)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", res)
        self.assertNotIn("tail_risk_metrics", res)
        self.assertNotIn("stream_payload", res)

    def test_graphical_format_full_payload(self):
        rand_id = uuid.uuid4().hex
        rand_score = round(random.uniform(10.0, 50.0), 2)
        rand_tail_key = uuid.uuid4().hex
        rand_tail_val = random.randint(100, 999)
        rand_stream_key = uuid.uuid4().hex
        rand_stream_val = uuid.uuid4().hex

        payload = {
            "portfolio_id": rand_id,
            "format": "dashboard",
            "adaptive_risk_score": rand_score,
            "tail_risk_metrics": {rand_tail_key: rand_tail_val},
            "stream_payload": {rand_stream_key: rand_stream_val},
        }

        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(res.get("portfolio_id"), rand_id)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("layout"), "graphical")
        self.assertEqual(res.get("adaptive_risk_score"), rand_score)
        self.assertEqual(res.get("tail_risk_metrics"), {rand_tail_key: rand_tail_val})
        self.assertEqual(res.get("stream_payload"), {rand_stream_key: rand_stream_val})

    def test_payload_uses_report_id_fallback(self):
        rand_report_id = uuid.uuid4().hex
        payload = {
            "report_id": rand_report_id,
            "format": "text_summary",
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_report_id, res)


if __name__ == "__main__":
    unittest.main()