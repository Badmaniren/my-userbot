import unittest
import uuid
import random
from skills import db_storage
from skills import market_portfolio_stress_monte_carlo_engine as mc_engine


class TestMarketPortfolioStressMonteCarloEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:10]}"
        self.initial_value = round(random.uniform(50000.0, 250000.0), 2)
        self.volatility = round(random.uniform(0.15, 0.35), 4)
        self.drift = round(random.uniform(0.01, 0.08), 4)

        portfolio_record = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        if not hasattr(db_storage, "_in_memory_db") or getattr(db_storage, "_in_memory_db") is None:
            setattr(db_storage, "_in_memory_db", {})
        db_storage._in_memory_db[self.portfolio_id] = portfolio_record

    def test_run_simulation_integration(self):
        engine = mc_engine.MonteCarloStressEngine()
        simulations = random.randint(15, 30)
        horizon_days = random.randint(3, 10)

        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations,
            horizon_days=horizon_days
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)

        self.assertEqual(len(result["simulation_results"]), simulations)
        for path in result["simulation_results"]:
            self.assertEqual(len(path), horizon_days)
            for step_val in path:
                self.assertIsInstance(step_val, float)
                self.assertGreater(step_val, 0.0)

        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["cvar_95"], float)
        self.assertGreaterEqual(result["cvar_95"], result["var_95"])

    def test_run_monte_carlo_stress_test_function(self):
        scenario_params = {
            "volatility": round(random.uniform(0.1, 0.4), 3),
            "drift": round(random.uniform(-0.05, 0.05), 3),
            "horizon_days": random.randint(2, 7)
        }
        iterations = random.randint(20, 40)
        test_val = round(random.uniform(10000.0, 90000.0), 2)
        test_port_id = f"port_fn_{uuid.uuid4().hex[:8]}"

        stress_result = mc_engine.run_monte_carlo_stress_test(
            portfolio_id=test_port_id,
            portfolio_value=test_val,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result["portfolio_id"], test_port_id)
        self.assertEqual(stress_result["initial_value"], test_val)
        self.assertEqual(stress_result["iterations"], iterations)
        self.assertTrue(stress_result["simulation_id"].startswith("sim_"))
        self.assertIsInstance(stress_result["var_95"], float)
        self.assertIsInstance(stress_result["expected_shortfall"], float)
        self.assertGreaterEqual(stress_result["expected_shortfall"], stress_result["var_95"])

    def test_export_report_passthrough(self):
        engine = mc_engine.MonteCarloStressEngine()
        random_report_id = f"rep_{uuid.uuid4().hex[:8]}"
        random_limit = round(random.uniform(500.0, 5000.0), 2)

        export_res = engine.export_report(random_report_id, random_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), random_report_id)
        self.assertEqual(export_res.get("loss_limit"), random_limit)


if __name__ == "__main__":
    unittest.main()