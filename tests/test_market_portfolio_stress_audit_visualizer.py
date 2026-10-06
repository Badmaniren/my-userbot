import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_deps = {
            "db_storage": f"db_{uuid.uuid4().hex[:8]}",
            "market_portfolio_stress_scenario_matrix_evaluator": f"eval_{uuid.uuid4().hex[:8]}"
        }
        self.visualizer_class = MarketPortfolioStressAuditVisualizer(**self.random_deps)

    def test_init_and_dependencies(self):
        self.assertEqual(self.visualizer_class.db_storage, self.random_deps["db_storage"])
        self.assertEqual(self.visualizer_class.dependencies, self.random_deps)

    def test_visualize_proxy_call(self):
        portfolio_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(1.0, 100.0), 2)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }
        
        result = self.visualizer_class.visualize(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_non_dict_payload(self):
        random_string = "".join(random.choices(string.ascii_letters, k=15))
        result = market_portfolio_stress_audit_visualizer(random_string)
        self.assertEqual(result, random_string)

        random_number = random.randint(1000, 99999)
        result_num = market_portfolio_stress_audit_visualizer(random_number)
        self.assertEqual(result_num, str(random_number))

    def test_text_summary_format_basic(self):
        report_id = uuid.uuid4().hex
        payload = {
            "report_id": report_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        expected_msg = f"Portfolio Stress Audit Summary for {report_id}: Data successfully audited and visualized."
        self.assertEqual(result, expected_msg)

    def test_text_summary_format_advanced(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:6]}"
        adaptive_score = round(random.uniform(0.1, 99.9), 4)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        format_type = "".join(random.choices(string.ascii_lowercase, k=8))
        payload = {
            "portfolio_id": portfolio_id,
            "format": format_type
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["layout"], "graphical")
        self.assertNotIn("adaptive_risk_score", result)
        self.assertNotIn("tail_risk_metrics", result)
        self.assertNotIn("stream_payload", result)

    def test_graphical_format_with_optional_fields(self):
        portfolio_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(10.0, 50.0), 2)
        tail_risk_metrics = {uuid.uuid4().hex: random.random() for _ in range(3)}
        stream_payload = {"stream_id": uuid.uuid4().hex, "data": random.randint(1, 100)}
        
        payload = {
            "portfolio_id": portfolio_id,
            "format": "graphical_custom",
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": tail_risk_metrics,
            "stream_payload": stream_payload
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["layout"], "graphical")
        self.assertEqual(result["adaptive_risk_score"], adaptive_score)
        self.assertEqual(result["tail_risk_metrics"], tail_risk_metrics)
        self.assertEqual(result["stream_payload"], stream_payload)


if __name__ == "__main__":
    unittest.main()