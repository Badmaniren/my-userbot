import unittest
import uuid
import random

from skills import (
    db_storage,
    market_anomaly_detector,
    market_portfolio_audit_compliance_hub,
    market_portfolio_stress_audit_visualizer,
    market_portfolio_stress_monte_carlo_engine
)

class TestIntegrationMonteCarloStressEngine(unittest.TestCase):
    def test_run_simulation_and_stress_test_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_value = round(random.uniform(50000.0, 150000.0), 2)
        volatility = round(random.uniform(0.1, 0.4), 2)
        drift = round(random.uniform(-0.05, 0.05), 4)

        if hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db[portfolio_id] = {
                "initial_value": initial_value,
                "volatility": volatility,
                "drift": drift
            }
        elif hasattr(db_storage, "save_portfolio"):
            try:
                db_storage.save_portfolio(portfolio_id, {
                    "initial_value": initial_value,
                    "volatility": volatility,
                    "drift": drift
                })
            except Exception:
                pass

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        simulations_count = random.randint(10, 50)
        horizon_days = random.randint(5, 30)

        result_engine = engine.run_simulation(portfolio_id, simulations_count, horizon_days)

        self.assertIn("portfolio_id", result_engine)
        self.assertEqual(result_engine["portfolio_id"], portfolio_id)
        self.assertIn("var_95", result_engine)
        self.assertIn("cvar_95", result_engine)
        self.assertIn("simulation_results", result_engine)
        self.assertEqual(len(result_engine["simulation_results"]), simulations_count)

        iterations_count = random.randint(10, 50)
        scenario_params = {
            "volatility": volatility,
            "drift": drift,
            "horizon_days": horizon_days
        }

        func_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=initial_value,
            scenario_params=scenario_params,
            iterations=iterations_count
        )

        self.assertIn("simulation_id", func_result)
        self.assertTrue(func_result["simulation_id"].startswith("sim_"))
        self.assertEqual(func_result["portfolio_id"], portfolio_id)
        self.assertEqual(func_result["iterations"], iterations_count)
        self.assertIn("var_95", func_result)
        self.assertIn("expected_shortfall", func_result)

        with self.assertRaises(ValueError):
            engine.run_simulation(portfolio_id, -5, horizon_days)

        with self.assertRaises(ValueError):
            market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
                portfolio_id=portfolio_id,
                portfolio_value=initial_value,
                scenario_params=scenario_params,
                iterations=0
            )

if __name__ == "__main__":
    unittest.main()