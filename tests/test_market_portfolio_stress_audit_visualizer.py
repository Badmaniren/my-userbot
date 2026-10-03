import unittest
import uuid
import random
from unittest.mock import patch
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_db = uuid.uuid4().hex
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(db_storage=self.random_db)

    def test_init_sets_dependencies(self):
        self.assertEqual(self.visualizer_instance.db_storage, self.random_db)
        self.assertIn("db_storage", self.visualizer_instance.dependencies)

    def test_visualize_delegates_correctly(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": round(random.uniform(1.0, 100.0), 2),
            "export_to_text_report": True
        }
        result = self.visualizer_instance.visualize(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn("Portfolio Stress Audit Summary", result)

    def test_non_dict_payload_returns_string(self):
        random_number = random.randint(1000, 99999)
        result = market_portfolio_stress_audit_visualizer(random_number)
        self.assertEqual(result, str(random_number))

    def test_text_summary_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "report_id": portfolio_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        expected_msg = (
            f"Portfolio Stress Audit Summary for {portfolio_id}: "
            f"Data successfully audited and visualized."
        )
        self.assertEqual(result, expected_msg)

    def test_text_summary_format_with_adaptive_score(self):
        portfolio_id = uuid.uuid4().hex
        risk_score = round(random.uniform(10.0, 99.9), 2)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": risk_score
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn(str(risk_score), result)
        self.assertIn("Adaptive Risk Score", result)

    def test_text_summary_format_with_export_text(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "export_to_text_report": True
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_returns_dict(self):
        portfolio_id = uuid.uuid4().hex
        risk_score = round(random.uniform(1.0, 50.0), 2)
        tail_metric = uuid.uuid4().hex
        stream_data = uuid.uuid4().hex

        payload = {
            "portfolio_id": portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": risk_score,
            "tail_risk_metrics": tail_metric,
            "stream_payload": stream_data
        }

        result = market_portfolio_stress_audit_visualizer(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), risk_score)
        self.assertEqual(result.get("tail_risk_metrics"), tail_metric)
        self.assertEqual(result.get("stream_payload"), stream_data)


if __name__ == "__main__":
    unittest.main()