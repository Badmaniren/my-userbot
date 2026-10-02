import unittest
import random
import uuid

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_stress_monte_carlo_engine


class TestMonteCarloStressEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = float(random.randint(50000, 500000))
        self.volatility = round(random.uniform(0.1, 0.4), 2)
        self.drift = round(random.uniform(-0.05, 0.05), 4)

        if not hasattr(db_storage, "_in_memory_db"):
            setattr(db_storage, "_in_memory_db", {})
        
        db_storage._in_memory_db[self.portfolio_id] = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

    def test_run_simulation_and_stress_test_integration(self):
        simulations_count = random.randint(100, 500)
        horizon = random.randint(5, 30)

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations_count,
            horizon_days=horizon
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertEqual(len(result["simulation_results"]), simulations_count)
        self.assertGreaterEqual(result["var_95"], 0.0)
        self.assertGreaterEqual(result["cvar_95"], 0.0)

        iterations = random.randint(50, 200)
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": horizon
        }

        standalone_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(standalone_result, dict)
        self.assertTrue(standalone_result["simulation_id"].startswith("sim_"))
        self.assertEqual(standalone_result["portfolio_id"], self.portfolio_id)
        self.assertEqual(standalone_result["iterations"], iterations)
        self.assertIn("var_95", standalone_result)
        self.assertIn("expected_shortfall", standalone_result)

        anomaly_mult = engine._get_anomaly_adjustment()
        self.assertIsInstance(anomaly_mult, float)


if __name__ == "__main__":
    unittest.main()