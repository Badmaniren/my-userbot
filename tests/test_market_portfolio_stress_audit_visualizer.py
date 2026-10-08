import unittest
import uuid
import random
from unittest.mock import MagicMock, patch
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_db = uuid.uuid4().hex
        self.visualizer_class = MarketPortfolioStressAuditVisualizer(db_storage=self.random_db)

    def test_init_sets_dependencies(self):
        self.assertEqual(self.visualizer_class.db_storage, self.random_db)

    def test_visualizer_class_delegates_to_function(self):
        portfolio_id = uuid.uuid4().hex
        payload = {"portfolio_id": portfolio_id, "format": "text_summary"}
        res_class = self.visualizer_class.visualize(payload)
        res_func = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(res_class, res_func)

    def test_payload_not_dict_returns_string(self):
        random_str = uuid.uuid4().hex
        result = market_portfolio_stress_audit_visualizer(random_str)
        self.assertEqual(result, random_str)

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
        score = random.randint(100, 999)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": score
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(str(score), result)
        self.assertIn("Adaptive Risk Score", result)

    def test_text_summary_format_with_export_text(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "export_to_text_report": True
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn("Exported to text report successfully", result)

    def test_graphical_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "graphical"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")

    def test_graphical_format_with_all_optional_fields(self):
        portfolio_id = uuid.uuid4().hex
        score = random.random() * 100
        tail_metrics = {uuid.uuid4().hex: random.randint(1, 10)}
        stream = uuid.uuid4().hex

        payload = {
            "portfolio_id": portfolio_id,
            "format": uuid.uuid4().hex,  # Anything other than text_summary
            "adaptive_risk_score": score,
            "tail_risk_metrics": tail_metrics,
            "stream_payload": stream
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("adaptive_risk_score"), score)
        self.assertEqual(result.get("tail_risk_metrics"), tail_metrics)
        self.assertEqual(result.get("stream_payload"), stream)
        self.assertEqual(result.get("layout"), "graphical")


if __name__ == "__main__":
    unittest.main()