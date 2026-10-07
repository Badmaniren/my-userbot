import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_stress_testing_dashboard_aggregator import market_portfolio_stress_stress_testing_dashboard_aggregator
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_stress_scenario_matrix_evaluator import market_portfolio_stress_scenario_matrix_evaluator
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter
from skills.market_portfolio_alert_dispatcher import market_portfolio_alert_dispatcher
from skills.db_storage import db_storage

class TestMarketPortfolioStressTestingDashboardAggregatorIntegration(unittest.TestCase):

    def test_dashboard_aggregator_real_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulation_runs = random.randint(100, 1000)
        confidence_level = round(random.uniform(0.95, 0.99), 4)
        
        mc_input = {
            "portfolio_id": portfolio_id,
            "runs": simulation_runs,
            "horizon_days": random.randint(10, 30)
        }
        mc_result = market_portfolio_stress_monte_carlo_engine(mc_input)
        self.assertIsNotNone(mc_result)

        matrix_input = {
            "portfolio_id": portfolio_id,
            "shock_steps": random.randint(3, 10)
        }
        matrix_result = market_portfolio_stress_scenario_matrix_evaluator(matrix_input)
        self.assertIsNotNone(matrix_result)

        var_input = {
            "portfolio_id": portfolio_id,
            "confidence": confidence_level
        }
        var_result = market_portfolio_var_liquidity_core(var_input)
        self.assertIsNotNone(var_result)

        aggregator_payload = {
            "dashboard_id": f"dash_{uuid.uuid4().hex}",
            "portfolio_id": portfolio_id,
            "monte_carlo_data": mc_result,
            "scenario_matrix_data": matrix_result,
            "var_data": var_result,
            "include_alerts": True
        }
        
        aggregator_response = market_portfolio_stress_stress_testing_dashboard_aggregator(aggregator_payload)
        
        self.assertIsInstance(aggregator_response, dict)
        self.assertIn("status", aggregator_response)
        self.assertEqual(aggregator_response["status"], "success")
        self.assertIn("report_id", aggregator_response)

        report_id = aggregator_response["report_id"]
        
        reporter_check = market_portfolio_stress_reporter({"report_id": report_id})
        self.assertIsNotNone(reporter_check)

        alert_dispatch_check = market_portfolio_alert_dispatcher({
            "source": "dashboard_aggregator",
            "portfolio_id": portfolio_id,
            "report_id": report_id
        })
        self.assertIsNotNone(alert_dispatch_check)

        stored_data = db_storage({"action": "get", "key": report_id})
        self.assertIsNotNone(stored_data)

if __name__ == "__main__":
    unittest.main()