import unittest
import uuid
import random
from unittest.mock import patch, MagicMock
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)

class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.adaptive_score = round(random.uniform(1.0, 100.0), 2)
        self.visualizer = MarketPortfolioStressAuditVisualizer(db_storage=f"db_{uuid.uuid4().hex[:6]}")

    def test_visualizer_init_and_class_method(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.adaptive_score,
            "export_to_text_report": True
        }
        res_instance = self.visualizer.visualize(payload)
        res_function = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIn(self.portfolio_id, res_instance)
        self.assertIn(str(self.adaptive_score), res_instance)
        self.assertEqual(res_instance, res_function)

    def test_text_summary_format(self):
        payload = {
            "report_id": self.portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.adaptive_score,
            "export_to_text_report": False
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, str)
        self.assertIn(self.portfolio_id, result)
        self.assertIn("Portfolio Stress Audit Summary", result)
        self.assertIn(str(self.adaptive_score), result)
        self.assertNotIn("Exported to text report successfully.", result)

    def test_graphical_format_with_all_fields(self):
        tail_risk = {"var_95": random.random(), "cvar_95": random.random()}
        stream_data = {"stream_id": uuid.uuid4().hex, "active": True}
        monte_carlo = {"simulations": random.randint(100, 1000), "mean": random.uniform(-10, 10)}

        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.adaptive_score,
            "tail_risk_metrics": tail_risk,
            "stream_payload": stream_data,
            "monte_carlo_simulation": monte_carlo
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.adaptive_score)
        self.assertEqual(result.get("tail_risk_metrics"), tail_risk)
        self.assertEqual(result.get("stream_payload"), stream_data)
        self.assertEqual(result.get("monte_carlo_simulation"), monte_carlo)

    def test_non_dict_payload(self):
        random_string = uuid.uuid4().hex
        result = market_portfolio_stress_audit_visualizer(random_string)
        self.assertEqual(result, random_string)

    def test_with_context_manager_patch(self):
        with patch("skills.market_portfolio_stress_audit_visualizer.market_portfolio_stress_audit_visualizer") as mock_visualizer:
            mock_response_val = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_visualizer.return_value = mock_response_val
            
            payload = {"portfolio_id": self.portfolio_id}
            res = self.visualizer.visualize(payload)
            self.assertEqual(res, mock_response_val)
            mock_visualizer.assert_called_once_with(payload)

if __name__ == "__main__":
    unittest.main()