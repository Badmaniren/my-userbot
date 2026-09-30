import unittest
import uuid
import random
from skills.db_storage import db_storage
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.market_portfolio_stress_monte_carlo_resiliency_engine import (
    market_portfolio_stress_monte_carlo_resiliency_engine,
    start_new
)

class TestMarketPortfolioStressMonteCarloResiliencyEngineIntegration(unittest.TestCase):

    def test_resiliency_engine_integration_flow(self):
        portfolio_id = str(uuid.uuid4())
        total_value = round(random.uniform(50000.0, 500000.0), 2)
        shock_factor = round(random.uniform(0.05, 0.5), 2)
        iterations = random.randint(100, 5000)

        valuation_payload = {
            "portfolio_id": portfolio_id,
            "total_value": total_value
        }
        valuation_result = market_portfolio_valuation(valuation_payload)

        scenario_payload = {
            "portfolio_id": portfolio_id,
            "shock_factor": shock_factor,
            "baseline_valuation": valuation_result
        }
        scenario_result = market_portfolio_scenario_simulator(scenario_payload)

        engine_payload = {
            "portfolio_id": portfolio_id,
            "baseline_valuation": {"total_value": total_value},
            "shock_factor": shock_factor,
            "scenario_data": scenario_result
        }

        engine_result = market_portfolio_stress_monte_carlo_resiliency_engine(engine_payload)

        self.assertEqual(engine_result.get("portfolio_id"), portfolio_id)
        self.assertIn("resiliency_score", engine_result)
        self.assertIn("var_95", engine_result)
        self.assertIn("expected_shortfall", engine_result)
        self.assertEqual(engine_result.get("status"), "success")

        expected_resiliency = max(0.0, min(100.0, 100.0 * (1.0 - shock_factor)))
        self.assertAlmostEqual(engine_result.get("resiliency_score"), expected_resiliency)

        expected_var_95 = total_value * shock_factor * 0.8
        self.assertAlmostEqual(engine_result.get("var_95"), expected_var_95)

        db_storage({
            "action": "save_stress_test",
            "portfolio_id": portfolio_id,
            "metrics": engine_result
        })

        start_new_result = start_new(iterations=iterations, shock_factor=shock_factor)
        self.assertEqual(start_new_result.get("iterations_processed"), iterations)
        self.assertEqual(start_new_result.get("applied_shock"), shock_factor)

if __name__ == "__main__":
    unittest.main()