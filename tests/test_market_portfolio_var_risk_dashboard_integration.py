import unittest
import uuid
import random
import os

from skills.market_portfolio_var_risk_dashboard import (
    market_portfolio_var_risk_dashboard,
)
from skills.market_portfolio_stress_monte_carlo_engine import (
    market_portfolio_stress_monte_carlo_engine,
)
from skills.db_storage import db_storage


class TestMarketPortfolioVarRiskDashboardIntegration(unittest.TestCase):

    def test_var_risk_dashboard_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulation_runs = random.randint(1000, 5000)
        confidence_level = round(random.uniform(0.95, 0.99), 4)

        monte_carlo_input = {
            "portfolio_id": portfolio_id,
            "runs": simulation_runs,
            "confidence": confidence_level,
            "initial_value": round(random.uniform(10000.0, 1000000.0), 2),
        }

        mc_result = market_portfolio_stress_monte_carlo_engine(
            monte_carlo_input
        )

        self.assertIsInstance(mc_result, dict)
        self.assertIn("simulation_id", mc_result)

        dashboard_input = {
            "portfolio_id": portfolio_id,
            "simulation_id": mc_result["simulation_id"],
            "confidence_level": confidence_level,
        }

        dashboard_report = market_portfolio_var_risk_dashboard(dashboard_input)

        self.assertIsInstance(dashboard_report, dict)
        self.assertIn("report_id", dashboard_report)
        self.assertIn("var_value", dashboard_report)
        self.assertIn("potential_drawdown", dashboard_report)

        report_id = dashboard_report["report_id"]
        stored_data = db_storage({"action": "get", "key": report_id})

        self.assertIsInstance(stored_data, dict)
        self.assertEqual(stored_data.get("portfolio_id"), portfolio_id)
        self.assertEqual(stored_data.get("simulation_id"), mc_result["simulation_id"])


if __name__ == "__main__":
    unittest.main()