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
        self.random_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.random_adaptive_score = round(random.uniform(1.0, 99.9), 2)
        self.random_tail_metric = f"tail_{uuid.uuid4().hex[:6]}"
        self.random_stream_data = f"stream_{uuid.uuid4().hex[:6]}"

        self.db_mock = f"db_{uuid.uuid4().hex[:4]}"
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(db_storage=self.db_mock)

    def test_init_and_dependencies(self):
        self.assertEqual(self.visualizer_instance.db_storage, self.db_mock)
        self.assertIn("db_storage", self.visualizer_instance.dependencies)

    def test_visualize_wrapper_delegates_correctly(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.random_adaptive_score
        }
        res = self.visualizer_instance.visualize(payload)
        self.assertIn(self.random_portfolio_id, res)
        self.assertIn(str(self.random_adaptive_score), res)

    def test_non_dict_payload_returns_string(self):
        random_num = random.randint(1000, 99999)
        res = market_portfolio_stress_audit_visualizer(random_num)
        self.assertEqual(res, str(random_num))

        random_str = f"payload_{uuid.uuid4().hex[:6]}"
        res_str = market_portfolio_stress_audit_visualizer(random_str)
        self.assertEqual(res_str, random_str)

    def test_text_summary_format_basic(self):
        payload = {
            "report_id": self.random_portfolio_id,
            "format": "text_summary"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(self.random_portfolio_id, res)
        self.assertIn("Portfolio Stress Audit Summary", res)

    def test_text_summary_format_with_adaptive_score(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.random_adaptive_score,
            "export_to_text_report": True
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(self.random_portfolio_id, res)
        self.assertIn(str(self.random_adaptive_score), res)
        self.assertIn("Exported to text report successfully.", res)

    def test_graphical_format_basic(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "graphical"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), self.random_portfolio_id)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", res)

    def test_graphical_format_extended_payload(self):
        payload = {
            "report_id": self.random_portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.random_adaptive_score,
            "tail_risk_metrics": self.random_tail_metric,
            "stream_payload": self.random_stream_data
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), self.random_portfolio_id)
        self.assertEqual(res.get("adaptive_risk_score"), self.random_adaptive_score)
        self.assertEqual(res.get("tail_risk_metrics"), self.random_tail_metric)
        self.assertEqual(res.get("stream_payload"), self.random_stream_data)

    def test_format_fallback_to_graphical(self):
        random_format = f"fmt_{uuid.uuid4().hex[:5]}"
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": random_format
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("layout"), "graphical")
        self.assertEqual(res.get("portfolio_id"), self.random_portfolio_id)


if __name__ == "__main__":
    unittest.main()