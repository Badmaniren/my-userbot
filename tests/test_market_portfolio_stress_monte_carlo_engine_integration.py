import unittest
import uuid
import random

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_stress_monte_carlo_engine


class TestIntegrationMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        
        # Настройка реального хранилища без моков
        if hasattr(db_storage, "_in_memory_db") and isinstance(db_storage._in_memory_db, dict):
            db_storage._in_memory_db[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }

    def test_monte_carlo_engine_simulation_integration(self):
        simulations = random.randint(100, 500)
        horizon_days = random.randint(10, 30)

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations,
            horizon_days=horizon_days
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertEqual(len(result["simulation_results"]), simulations)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["cvar_95"], float)

    def test_standalone_stress_function_integration(self):
        iterations = random.randint(50, 200)
        scenario_params = {
            "volatility": round(random.uniform(0.15, 0.45), 4),
            "drift": round(random.uniform(-0.02, 0.02), 4),
            "horizon_days": random.randint(5, 15)
        }

        result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("initial_value"), self.initial_value)
        self.assertEqual(result.get("iterations"), iterations)
        self.assertIn("simulation_id", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)


if __name__ == "__main__":
    unittest.main()