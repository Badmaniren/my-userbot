import unittest
import uuid
import random
from skills import db_storage
from skills import market_portfolio_stress_monte_carlo_engine
from skills import market_portfolio_collector_agent
from skills import market_portfolio_valuation
from skills import market_portfolio_scenario_simulator


class IntegrationTestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.simulations_count = random.randint(100, 500)
        self.horizon_days = random.randint(5, 30)
        self.initial_capital = round(random.uniform(50000.0, 500000.0), 2)
        
        if not hasattr(db_storage, "fetch_portfolio"):
            setattr(db_storage, "fetch_portfolio", lambda pid: {
                "portfolio_id": pid,
                "initial_value": self.initial_capital,
                "volatility": 0.25,
                "drift": 0.02
            })
        else:
            if hasattr(db_storage, "_in_memory_db"):
                db_storage._in_memory_db[self.portfolio_id] = {
                    "portfolio_id": self.portfolio_id,
                    "initial_value": self.initial_capital,
                    "volatility": 0.25,
                    "drift": 0.02
                }

    def test_monte_carlo_engine_integration_workflow(self):
        collected_data = market_portfolio_collector_agent.collect_portfolio_data(
            self.portfolio_id, self.initial_capital
        )
        self.assertIsInstance(collected_data, dict)
        self.assertEqual(collected_data.get("portfolio_id"), self.portfolio_id)

        portfolio_val = market_portfolio_valuation.calculate_portfolio_value(collected_data)
        self.assertIsInstance(portfolio_val, (int, float))
        self.assertGreater(portfolio_val, 0)

        scenario_params = market_portfolio_scenario_simulator.generate_stress_scenario(
            volatility_factor=round(random.uniform(0.1, 0.5), 2)
        )
        self.assertIsInstance(scenario_params, dict)
        self.assertIn("volatility", scenario_params)

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        simulation_result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=self.simulations_count,
            horizon_days=self.horizon_days
        )

        self.assertIsInstance(simulation_result, dict)
        self.assertEqual(simulation_result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_95", simulation_result)
        self.assertIn("cvar_95", simulation_result)
        self.assertIn("simulation_results", simulation_result)
        self.assertEqual(len(simulation_result["simulation_results"]), self.simulations_count)

        standalone_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=portfolio_val,
            scenario_params=scenario_params,
            iterations=self.simulations_count
        )

        self.assertIsInstance(standalone_result, dict)
        self.assertIn("simulation_id", standalone_result)
        self.assertTrue(standalone_result["simulation_id"].startswith("sim_"))
        self.assertEqual(standalone_result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(standalone_result.get("iterations"), self.simulations_count)
        self.assertIsInstance(standalone_result.get("var_95"), float)
        self.assertIsInstance(standalone_result.get("expected_shortfall"), float)


if __name__ == "__main__":
    unittest.main()