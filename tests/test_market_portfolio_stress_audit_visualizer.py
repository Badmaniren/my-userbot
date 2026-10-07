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
        self.random_deps = {
            "db_storage": uuid.uuid4().hex,
            "market_portfolio_stress_audit_visualizer": uuid.uuid4().hex,
            "market_portfolio_api_gateway": uuid.uuid4().hex
        }
        self.visualizer = MarketPortfolioStressAuditVisualizer(**self.random_deps)

    def test_init_and_dependencies(self):
        self.assertEqual(self.visualizer.db_storage, self.random_deps["db_storage"])
        self.assertEqual(self.visualizer.dependencies, self.random_deps)

    def test_visualize_delegation(self):
        random_portfolio_id = uuid.uuid4().hex
        payload = {"portfolio_id": random_portfolio_id, "format": "text_summary"}
        
        with patch("skills.market_portfolio_stress_audit_visualizer.market_portfolio_stress_audit_visualizer") as mock_func:
            mock_return_value = uuid.uuid4().hex
            mock_func.return_value = mock_return_value
            
            result = self.visualizer.visualize(payload)
            mock_func.assert_called_once_with(payload)
            self.assertEqual(result, mock_return_value)

    def test_market_portfolio_stress_audit_visualizer_non_dict_payload(self):
        random_string = uuid.uuid4().hex
        result = market_portfolio_stress_audit_visualizer(random_string)
        self.assertEqual(result, str(random_string))

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

    def test_text_summary_format_with_adaptive_score_and_export(self):
        report_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(0.0, 100.0), 2)
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
        payload = {
            "portfolio_id": portfolio_id,
            "format": "graphical"
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", result)
        self.assertNotIn("tail_risk_metrics", result)
        self.assertNotIn("stream_payload", result)

    def test_graphical_format_extended_payload(self):
        portfolio_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(1.0, 50.0), 4)
        tail_metric_key = uuid.uuid4().hex
        tail_metric_val = random.randint(100, 999)
        tail_risk_metrics = {tail_metric_key: tail_metric_val}
        stream_payload = uuid.uuid4().hex

        payload = {
            "portfolio_id": portfolio_id,
            "format": uuid.uuid4().hex + "_graphical",
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": tail_risk_metrics,
            "stream_payload": stream_payload
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["layout"], "graphical")
        self.assertEqual(result["adaptive_risk_score"], adaptive_score)
        self.assertEqual(result["tail_risk_metrics"], tail_risk_metrics)
        self.assertEqual(result["stream_payload"], stream_payload)


if __name__ == "__main__":
    unittest.main()