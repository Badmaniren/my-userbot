import unittest
import uuid
import random
from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage
from skills import market_anomaly_detector

class TestIntegrationMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        
        if hasattr(db_storage, "_in_memory_db") and isinstance(db_storage._in_memory_db, dict):
            db_storage._in_memory_db[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }

    def test_run_simulation_integration(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        simulations = random.randint(50, 200)
        horizon_days = random.randint(5, 30)

        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations,
            horizon_days=horizon_days
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        
        sim_results = result["simulation_results"]
        self.assertEqual(len(sim_results), simulations)
        for path in sim_results:
            self.assertEqual(len(path), horizon_days)

        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["cvar_95"], float)

    def test_run_monte_carlo_stress_test_functional(self):
        iterations = random.randint(100, 300)
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": random.randint(10, 40)
        }

        stress_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(stress_result.get("initial_value"), self.initial_value)
        self.assertEqual(stress_result.get("iterations"), iterations)
        self.assertIn("simulation_id", stress_result)
        self.assertTrue(stress_result["simulation_id"].startswith("sim_"))
        self.assertIn("var_95", stress_result)
        self.assertIn("expected_shortfall", stress_result)

    def test_anomaly_adjustment_integration(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        if hasattr(market_anomaly_detector, "get_current_anomaly_multiplier"):
            multiplier = engine._get_anomaly_adjustment()
            self.assertIsInstance(multiplier, float)
            self.assertGreater(multiplier, 0.0)

    def test_export_and_stream_integration(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        report_id = f"rep_{uuid.uuid4().hex[:6]}"
        loss_limit = round(random.uniform(1000.0, 15000.0), 2)

        export_res = engine.export_report(report_id, loss_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)
        self.assertEqual(export_res.get("loss_limit"), loss_limit)

        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, str, bytes)))

if __name__ == "__main__":
    unittest.main()