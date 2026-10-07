import unittest
import uuid
import random
from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage


class TestIntegrationMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.4), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        
        if hasattr(db_storage, "_in_memory_db") and isinstance(db_storage._in_memory_db, dict):
            db_storage._in_memory_db[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }

    def test_run_simulation_integration(self):
        simulations = random.randint(50, 200)
        horizon_days = random.randint(5, 30)

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations,
            horizon_days=horizon_days
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertIn("simulation_results", result)
        
        sim_results = result.get("simulation_results")
        self.assertEqual(len(sim_results), simulations)
        for path in sim_results:
            self.assertEqual(len(path), horizon_days)

    def test_run_monte_carlo_stress_test_functional(self):
        iterations = random.randint(100, 300)
        scenario_params = {
            "volatility": round(random.uniform(0.15, 0.35), 4),
            "drift": round(random.uniform(-0.02, 0.02), 4),
            "horizon_days": random.randint(1, 15)
        }

        result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("simulation_id").startswith("sim_"))
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("initial_value"), self.initial_value)
        self.assertEqual(result.get("iterations"), iterations)
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)

    def test_export_report_integration(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        export_res = engine.export_report(report_id, loss_limit)

        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)
        self.assertEqual(export_res.get("loss_limit"), loss_limit)


if __name__ == "__main__":
    unittest.main()