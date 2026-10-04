import unittest
import uuid
import random

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_audit_compliance_hub
from skills import market_portfolio_stress_monte_carlo_engine


class TestIntegrationMonteCarloStressEngine(unittest.TestCase):

    def test_run_simulation_and_functional_pipeline(self):
        rand_suffix = uuid.uuid4().hex[:8]
        portfolio_id = f"port_{rand_suffix}"
        
        test_initial_value = float(random.randint(50000, 500000))
        test_volatility = round(random.uniform(0.1, 0.4), 4)
        test_drift = round(random.uniform(-0.05, 0.05), 4)

        if hasattr(db_storage, "_in_memory_db") and isinstance(db_storage._in_memory_db, dict):
            db_storage._in_memory_db[portfolio_id] = {
                "portfolio_id": portfolio_id,
                "initial_value": test_initial_value,
                "volatility": test_volatility,
                "drift": test_drift
            }

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        
        simulations_count = random.randint(50, 200)
        horizon_days = random.randint(5, 30)

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
        
        sim_results = result.get("simulation_results")
        self.assertEqual(len(sim_results), simulations_count)
        for path in sim_results:
            self.assertEqual(len(path), horizon_days)

        report_id = f"rep_{uuid.uuid4().hex}"
        loss_limit = float(random.randint(1000, 10000))
        export_res = engine.export_report(report_id, loss_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)
        self.assertEqual(export_res.get("loss_limit"), loss_limit)

        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, list, str, bytes, tuple)))

    def test_standalone_stress_test_function(self):
        rand_suffix = uuid.uuid4().hex[:8]
        portfolio_id = f"port_fn_{rand_suffix}"
        portfolio_value = float(random.randint(10000, 1000000))
        
        scenario_params = {
            "volatility": round(random.uniform(0.15, 0.5), 4),
            "drift": round(random.uniform(-0.1, 0.1), 4),
            "horizon_days": random.randint(1, 15)
        }
        iterations = random.randint(30, 150)

        res = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), portfolio_id)
        self.assertEqual(res.get("initial_value"), portfolio_value)
        self.assertEqual(res.get("iterations"), iterations)
        self.assertIn("simulation_id", res)
        self.assertTrue(res["simulation_id"].startswith("sim_"))
        self.assertIn("var_95", res)
        self.assertIn("expected_shortfall", res)


if __name__ == "__main__":
    unittest.main()