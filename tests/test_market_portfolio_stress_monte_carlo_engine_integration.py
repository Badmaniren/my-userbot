import unittest
import uuid
import random
from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage


class TestIntegrationMonteCarloStressEngine(unittest.TestCase):

    def test_run_simulation_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_value = round(random.uniform(50000.0, 500000.0), 2)
        volatility = round(random.uniform(0.1, 0.4), 4)
        drift = round(random.uniform(-0.05, 0.05), 4)
        
        if hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db[portfolio_id] = {
                "portfolio_id": portfolio_id,
                "initial_value": initial_value,
                "volatility": volatility,
                "drift": drift
            }

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        simulations_count = random.randint(50, 200)
        horizon_days = random.randint(5, 30)

        result = engine.run_simulation(portfolio_id, simulations=simulations_count, horizon_days=horizon_days)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        
        sim_results = result.get("simulation_results")
        self.assertEqual(len(sim_results), simulations_count)
        for path in sim_results:
            self.assertEqual(len(path), horizon_days)

    def test_run_monte_carlo_stress_test_function(self):
        portfolio_id = f"stress_port_{uuid.uuid4().hex[:8]}"
        portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        iterations = random.randint(100, 500)
        
        scenario_params = {
            "volatility": round(random.uniform(0.15, 0.5), 4),
            "drift": round(random.uniform(-0.1, 0.05), 4),
            "horizon_days": random.randint(1, 15)
        }

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
        self.assertTrue(result.get("simulation_id").startswith("sim_"))
        self.assertIsInstance(result.get("var_95"), float)
        self.assertIsInstance(result.get("expected_shortfall"), float)

    def test_engine_auxiliary_methods(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(5000.0, 50000.0), 2)

        export_res = engine.export_report(report_id, loss_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)
        self.assertEqual(export_res.get("loss_limit"), loss_limit)

        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, list, str, bytes)))


if __name__ == "__main__":
    unittest.main()