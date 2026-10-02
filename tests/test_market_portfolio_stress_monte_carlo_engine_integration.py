import unittest
import uuid
import random

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_stress_monte_carlo_engine


class TestIntegrationMonteCarloStressEngine(unittest.TestCase):

    def test_monte_carlo_simulation_and_audit_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_val = round(random.uniform(50000.0, 500000.0), 2)
        vol = round(random.uniform(0.1, 0.4), 2)
        drift_val = round(random.uniform(-0.05, 0.05), 4)

        if hasattr(db_storage, "_in_memory_db") and isinstance(db_storage._in_memory_db, dict):
            db_storage._in_memory_db[portfolio_id] = {
                "portfolio_id": portfolio_id,
                "initial_value": initial_val,
                "volatility": vol,
                "drift": drift_val
            }
        elif hasattr(db_storage, "store_portfolio"):
            try:
                db_storage.store_portfolio(portfolio_id, {"initial_value": initial_val, "volatility": vol})
            except Exception:
                pass

        simulations_count = random.randint(100, 500)
        horizon = random.randint(5, 30)

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        result = engine.run_simulation(portfolio_id=portfolio_id, simulations=simulations_count, horizon_days=horizon)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertIn("simulation_results", result)
        self.assertEqual(len(result["simulation_results"]), simulations_count)

        iterations = random.randint(50, 200)
        scenario_params = {
            "volatility": vol,
            "drift": drift_val,
            "horizon_days": horizon
        }

        standalone_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=initial_val,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(standalone_result, dict)
        self.assertEqual(standalone_result.get("portfolio_id"), portfolio_id)
        self.assertEqual(standalone_result.get("initial_value"), initial_val)
        self.assertEqual(standalone_result.get("iterations"), iterations)
        self.assertIn("simulation_id", standalone_result)
        self.assertTrue(standalone_result["simulation_id"].startswith("sim_"))


if __name__ == "__main__":
    unittest.main()