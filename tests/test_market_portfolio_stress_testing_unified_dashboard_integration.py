import unittest
import uuid
import random
import io
import datetime
from skills.market_portfolio_stress_testing_unified_dashboard import (
    MarketPortfolioStressTestingUnifiedDashboard,
    market_portfolio_stress_testing_unified_dashboard
)

class TestMarketPortfolioStressTestingUnifiedDashboardIntegration(unittest.TestCase):
    def test_unified_dashboard_integration(self):
        rand_portfolio_id = f"port_{uuid.uuid4()}"
        rand_event_token = f"token_{uuid.uuid4()}"
        rand_task_id = f"task_{uuid.uuid4()}"

        monte_carlo_val = random.uniform(1000.0, 50000.0)
        var_val = random.uniform(50.0, 500.0)
        scenario_val = random.randint(1, 10)

        dashboard_input = {
            "portfolio_id": rand_portfolio_id,
            "monte_carlo_metrics": {"simulated_value": monte_carlo_val},
            "var_metrics": {"var_95": var_val},
            "scenario_metrics": {"active_scenarios": scenario_val},
            "export_format": "json"
        }

        func_result = market_portfolio_stress_testing_unified_dashboard(dashboard_input)

        self.assertIn("dashboard_id", func_result)
        self.assertEqual(func_result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(func_result["monte_carlo_metrics"]["simulated_value"], monte_carlo_val)
        self.assertEqual(func_result["var_metrics"]["var_95"], var_val)
        self.assertEqual(func_result["scenario_metrics"]["active_scenarios"], scenario_val)

        dashboard_instance = MarketPortfolioStressTestingUnifiedDashboard()

        agg_result = dashboard_instance.aggregate_stress_metrics(rand_portfolio_id)
        self.assertIsInstance(agg_result, dict)
        self.assertEqual(agg_result.get("portfolio_id"), rand_portfolio_id)
        self.assertIn("monte_carlo", agg_result)
        self.assertIn("var_cvar", agg_result)
        self.assertIn("scenario_matrix", agg_result)

        vis_result = dashboard_instance.visualize_dashboard(rand_task_id)
        self.assertIsInstance(vis_result, io.BytesIO)
        vis_content = vis_result.read()
        self.assertIsInstance(vis_content, bytes)
        self.assertGreater(len(vis_content), 0)

        report_result = dashboard_instance.generate_audit_and_report(rand_event_token)
        self.assertIsInstance(report_result, dict)

if __name__ == "__main__":
    unittest.main()