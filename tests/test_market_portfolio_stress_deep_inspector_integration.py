import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_deep_inspector import inspect_portfolio_stress_vulnerabilities
from skills.market_portfolio_scenario_simulator import simulate_stress_scenario
from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_simulation

class IntegrationTestMarketPortfolioStressDeepInspector(unittest.TestCase):
    def test_inspect_portfolio_stress_vulnerabilities_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_id = f"scen_{random.randint(1000, 9999)}"

        scenario_data = simulate_stress_scenario(portfolio_id=portfolio_id, scenario_id=scenario_id)
        monte_carlo_metrics = run_monte_carlo_simulation(portfolio_id=portfolio_id, iterations=random.randint(10, 100))

        result = inspect_portfolio_stress_vulnerabilities(
            portfolio_id=portfolio_id,
            scenario_data=scenario_data,
            monte_carlo_metrics=monte_carlo_metrics
        )

        self.assertIn("inspection_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["scenario_id"], scenario_id)
        self.assertEqual(result["mc_metrics"], monte_carlo_metrics)
        self.assertIn("vulnerabilities", result)

        report_path = result.get("report_file_path")
        self.assertIsNotNone(report_path)
        self.assertTrue(os.path.exists(report_path))

        if os.path.exists(report_path):
            os.remove(report_path)

if __name__ == "__main__":
    unittest.main()