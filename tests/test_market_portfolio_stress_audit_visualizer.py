import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)

class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.rand_portfolio_id = uuid.uuid4().hex
        self.rand_report_id = uuid.uuid4().hex
        self.rand_score = round(random.uniform(1.0, 100.0), 2)
        self.rand_db = MagicMock()
        self.rand_simulator = MagicMock()
        self.rand_reporter = MagicMock()
        
        self.visualizer = MarketPortfolioStressAuditVisualizer(
            db_storage=self.rand_db,
            market_portfolio_scenario_simulator=self.rand_simulator,
            market_report_generator=self.rand_reporter
        )

    def test_init_and_dependencies(self):
        self.assertEqual(self.visualizer.db_storage, self.rand_db)
        self.assertIn("market_portfolio_scenario_simulator", self.visualizer.dependencies)
        self.assertIn("market_report_generator", self.visualizer.dependencies)

    def test_visualize_invalid_payload_type(self):
        rand_invalid_payload = "".join(random.choices(string.ascii_letters, k=10))
        result = self.visualizer.visualize(rand_invalid_payload)
        self.assertEqual(result, str(rand_invalid_payload))

    def test_visualize_text_summary_format(self):
        payload = {
            "portfolio_id": self.rand_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.rand_score,
            "export_to_text_report": True
        }
        result = self.visualizer.visualize(payload)
        self.assertIn(self.rand_portfolio_id, result)
        self.assertIn(str(self.rand_score), result)
        self.assertIn("Exported to text report successfully", result)

    def test_visualize_graphical_format(self):
        payload = {
            "report_id": self.rand_report_id,
            "format": "graphical",
            "adaptive_risk_score": self.rand_score
        }
        result = self.visualizer.visualize(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.rand_report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.rand_score)

    def test_standalone_function_text_summary(self):
        payload = {
            "portfolio_id": self.rand_portfolio_id,
            "format": "text_summary"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertTrue(isinstance(res, str))
        self.assertIn(self.rand_portfolio_id, res)

    def test_standalone_function_graphical(self):
        payload = {
            "report_id": self.rand_report_id,
            "format": "chart"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], self.rand_report_id)
        self.assertEqual(res["layout"], "graphical")

    def test_external_data_integration_mocking(self):
        rand_simulated_metric = random.randint(500, 5000)
        rand_report_content = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_audit_visualizer.market_portfolio_stress_audit_visualizer") as mock_func:
            mock_func.return_value = {
                "portfolio_id": self.rand_portfolio_id,
                "simulated_metric": rand_simulated_metric,
                "report": rand_report_content,
                "status": "success"
            }
            
            payload = {
                "portfolio_id": self.rand_portfolio_id,
                "format": "advanced"
            }
            
            res = self.visualizer.visualize(payload)
            self.assertEqual(res["simulated_metric"], rand_simulated_metric)
            self.assertEqual(res["report"], rand_report_content)
            mock_func.assert_called_once_with(payload)

if __name__ == "__main__":
    unittest.main()