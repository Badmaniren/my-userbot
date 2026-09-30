import unittest
import uuid
import random

from skills import db_storage
from skills import market_portfolio_collector_agent
from skills import market_portfolio_valuation
from skills import market_portfolio_scenario_simulator
from skills import market_portfolio_stress_monte_carlo_engine


class IntegrationTestMarketPortfolioStressMonteCarloEngine(unittest.TestCase):

    def test_run_monte_carlo_stress_test_integration(self):
        random_suffix = uuid.uuid4().hex[:8]
        portfolio_id = f"port_int_{random_suffix}"
        capital = round(random.uniform(50000.0, 500000.0), 2)
        iterations = random.randint(100, 1000)

        portfolio_data = market_portfolio_collector_agent.collect_portfolio_data(portfolio_id, capital)
        portfolio_value = market_portfolio_valuation.calculate_portfolio_value(portfolio_data)
        scenario_params = market_portfolio_scenario_simulator.generate_stress_scenario(volatility_factor=0.25)

        result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("initial_value"), portfolio_value)
        self.assertEqual(result.get("iterations"), iterations)
        self.assertIn("simulation_id", result)
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)

        simulation_id = result["simulation_id"]
        self.assertTrue(simulation_id.startswith("sim_"))

        db_storage.save_stress_test_result(simulation_id, result)
        fetched_result = db_storage.get_stress_test_result(simulation_id)

        self.assertIsInstance(fetched_result, dict)
        self.assertEqual(fetched_result.get("simulation_id"), simulation_id)
        self.assertEqual(fetched_result.get("portfolio_id"), portfolio_id)
        self.assertEqual(fetched_result.get("var_95"), result["var_95"])

    def test_monte_carlo_stress_engine_class_integration(self):
        random_suffix = uuid.uuid4().hex[:8]
        portfolio_id = f"port_cls_{random_suffix}"
        simulations_count = random.randint(50, 200)
        horizon_days = random.randint(1, 10)

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        result = engine.run_simulation(
            portfolio_id=portfolio_id,
            simulations=simulations_count,
            horizon_days=horizon_days
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertEqual(len(result.get("simulation_results")), simulations_count)


if __name__ == "__main__":
    unittest.main()