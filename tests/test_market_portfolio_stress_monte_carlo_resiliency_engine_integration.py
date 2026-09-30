import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_monte_carlo_resiliency_engine import market_portfolio_stress_monte_carlo_resiliency_engine
from skills.db_storage import db_storage
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_valuation import market_portfolio_valuation

class TestMarketPortfolioStressMonteCarloResiliencyEngineIntegration(unittest.TestCase):
    def test_monte_carlo_resiliency_pipeline(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_value = round(random.uniform(50000.0, 500000.0), 2)
        simulations_count = random.randint(100, 1000)
        shock_factor = round(random.uniform(0.1, 0.5), 4)

        valuation_data = {
            "portfolio_id": portfolio_id,
            "total_value": initial_value,
            "assets": [
                {"ticker": "BTC", "allocation": 0.5, "value": initial_value * 0.5},
                {"ticker": "ETH", "allocation": 0.5, "value": initial_value * 0.5}
            ]
        }
        valuation_res = market_portfolio_valuation(valuation_data)
        self.assertIsNotNone(valuation_res)

        scenario_data = {
            "portfolio_id": portfolio_id,
            "shock_magnitude": shock_factor,
            "simulations": simulations_count
        }
        scenario_res = market_portfolio_scenario_simulator(scenario_data)
        self.assertIsNotNone(scenario_res)

        engine_payload = {
            "portfolio_id": portfolio_id,
            "baseline_valuation": valuation_res,
            "scenario": scenario_res,
            "simulations_count": simulations_count,
            "shock_factor": shock_factor,
            "run_uuid": uuid.uuid4().hex
        }

        resiliency_result = market_portfolio_stress_monte_carlo_resiliency_engine(engine_payload)

        self.assertIsInstance(resiliency_result, dict)
        self.assertIn("resiliency_score", resiliency_result)
        self.assertIn("var_95", resiliency_result)
        self.assertIn("expected_shortfall", resiliency_result)
        self.assertEqual(resiliency_result.get("portfolio_id"), portfolio_id)

        db_payload = {
            "id": f"res_{uuid.uuid4().hex}",
            "portfolio_id": portfolio_id,
            "metrics": resiliency_result
        }
        db_save_res = db_storage(db_payload)
        self.assertIsNotNone(db_save_res)

if __name__ == "__main__":
    unittest.main()