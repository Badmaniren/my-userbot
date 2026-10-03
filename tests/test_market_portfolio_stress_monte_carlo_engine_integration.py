import unittest
import uuid
import random
from skills import db_storage
from skills import market_portfolio_collector_agent
from skills import market_portfolio_stress_monte_carlo_engine


class TestMonteCarloStressEngineIntegration(unittest.TestCase):

    def test_end_to_end_monte_carlo_stress_simulation(self):
        portfolio_id = f"test_port_{uuid.uuid4().hex[:8]}"
        initial_value = round(random.uniform(50000.0, 500000.0), 2)
        volatility = round(random.uniform(0.1, 0.5), 2)
        drift = round(random.uniform(-0.05, 0.05), 4)

        portfolio_payload = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_value,
            "volatility": volatility,
            "drift": drift
        }

        db_storage.save_portfolio(portfolio_id, portfolio_payload)

        collected_data = market_portfolio_collector_agent.collect_portfolio_metrics(portfolio_id)
        self.assertIsNotNone(collected_data)

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        simulations_count = random.randint(100, 500)
        horizon_days = random.randint(5, 30)

        result = engine.run_simulation(portfolio_id, simulations=simulations_count, horizon_days=horizon_days)

        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertEqual(len(result["simulation_results"]), simulations_count)

        iterations = random.randint(50, 200)
        scenario_params = {
            "volatility": volatility,
            "drift": drift,
            "horizon_days": horizon_days
        }

        standalone_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIn("simulation_id", standalone_result)
        self.assertTrue(standalone_result["simulation_id"].startswith("sim_"))
        self.assertEqual(standalone_result["portfolio_id"], portfolio_id)
        self.assertEqual(standalone_result["initial_value"], initial_value)
        self.assertEqual(standalone_result["iterations"], iterations)
        self.assertIsInstance(standalone_result["var_95"], float)
        self.assertIsInstance(standalone_result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()