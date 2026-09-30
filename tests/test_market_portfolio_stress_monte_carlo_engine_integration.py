import unittest
import uuid
import random
import os

from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.db_storage import db_storage


class TestMarketPortfolioStressMonteCarloEngineIntegration(unittest.TestCase):

    def test_monte_carlo_stress_simulation_pipeline(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_capital = round(random.uniform(50000.0, 500000.0), 2)
        simulations_count = random.randint(100, 1000)
        horizon_days = random.randint(30, 365)

        valuation_data = {
            "portfolio_id": portfolio_id,
            "capital": initial_capital,
            "assets": [
                {"ticker": "AAPL", "weight": 0.5, "volatility": 0.2},
                {"ticker": "MSFT", "weight": 0.5, "volatility": 0.25}
            ]
        }
        valuation_result = market_portfolio_valuation(valuation_data)
        self.assertIsNotNone(valuation_result)

        scenario_config = {
            "portfolio_id": portfolio_id,
            "horizon_days": horizon_days,
            "stress_factor": round(random.uniform(1.1, 2.5), 2)
        }
        scenario_result = market_portfolio_scenario_simulator(scenario_config)
        self.assertIsInstance(scenario_result, dict)

        engine_payload = {
            "simulation_id": f"sim_{uuid.uuid4().hex}",
            "portfolio_id": portfolio_id,
            "simulations_count": simulations_count,
            "horizon_days": horizon_days,
            "base_valuation": valuation_result,
            "scenario_parameters": scenario_result
        }

        simulation_output = market_portfolio_stress_monte_carlo_engine(engine_payload)

        self.assertIsInstance(simulation_output, dict)
        self.assertIn("simulation_id", simulation_output)
        self.assertEqual(simulation_output["simulation_id"], engine_payload["simulation_id"])
        self.assertIn("var_95", simulation_output)
        self.assertIn("expected_shortfall", simulation_output)

        stored_record = db_storage({
            "action": "get",
            "table": "monte_carlo_simulations",
            "id": engine_payload["simulation_id"]
        })
        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record.get("portfolio_id"), portfolio_id)


if __name__ == "__main__":
    unittest.main()