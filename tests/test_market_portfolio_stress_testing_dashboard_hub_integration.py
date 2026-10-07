import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_testing_dashboard_hub import (
    market_portfolio_stress_testing_dashboard_hub
)
from skills.market_portfolio_stress_monte_carlo_engine import (
    market_portfolio_stress_monte_carlo_engine
)
from skills.market_portfolio_scenario_simulator import (
    market_portfolio_scenario_simulator
)
from skills.db_storage import db_storage

class IntegrationTestMarketPortfolioStressTestingDashboardHub(unittest.TestCase):
    def test_dashboard_hub_integration_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulation_runs = random.randint(100, 1000)
        confidence_level = round(random.uniform(0.95, 0.99), 4)
        
        monte_carlo_result = market_portfolio_stress_monte_carlo_engine(
            portfolio_id=portfolio_id,
            runs=simulation_runs,
            confidence=confidence_level
        )
        
        self.assertIsInstance(monte_carlo_result, dict)
        self.assertIn("simulation_id", monte_carlo_result)
        
        scenario_name = f"stress_scenario_{uuid.uuid4().hex[:6]}"
        shock_magnitude = round(random.uniform(-0.40, -0.10), 2)
        
        scenario_result = market_portfolio_scenario_simulator(
            portfolio_id=portfolio_id,
            scenario=scenario_name,
            shock=shock_magnitude
        )
        
        self.assertIsInstance(scenario_result, dict)
        self.assertIn("scenario_id", scenario_result)
        
        dashboard_report_id = f"dash_{uuid.uuid4().hex}"
        dashboard_output = market_portfolio_stress_testing_dashboard_hub(
            dashboard_id=dashboard_report_id,
            portfolio_id=portfolio_id,
            monte_carlo_data=monte_carlo_result,
            scenario_data=scenario_result
        )
        
        self.assertIsInstance(dashboard_output, dict)
        self.assertEqual(dashboard_output.get("dashboard_id"), dashboard_report_id)
        self.assertEqual(dashboard_output.get("portfolio_id"), portfolio_id)
        self.assertIn("aggregated_metrics", dashboard_output)
        
        stored_record = db_storage(
            action="get",
            key=dashboard_report_id
        )
        
        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record.get("portfolio_id"), portfolio_id)

if __name__ == "__main__":
    unittest.main()