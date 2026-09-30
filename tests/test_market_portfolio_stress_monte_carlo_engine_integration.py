import unittest
import uuid
import random
from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway

class TestIntegrationMonteCarloStressEngine(unittest.TestCase):
    def test_end_to_end_simulation_and_export_flow(self):
        rand_suffix = uuid.uuid4().hex[:8]
        portfolio_id = f"port_int_{rand_suffix}"
        initial_val = round(random.uniform(50000.0, 500000.0), 2)
        vol = round(random.uniform(0.1, 0.4), 4)
        drift_val = round(random.uniform(-0.05, 0.05), 4)

        if hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db[portfolio_id] = {
                "portfolio_id": portfolio_id,
                "initial_value": initial_val,
                "volatility": vol,
                "drift": drift_val
            }

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        
        simulations_count = random.randint(50, 200)
        horizon = random.randint(5, 30)
        
        sim_result = engine.run_simulation(
            portfolio_id=portfolio_id,
            simulations=simulations_count,
            horizon_days=horizon
        )

        self.assertIsInstance(sim_result, dict)
        self.assertEqual(sim_result.get("portfolio_id"), portfolio_id)
        self.assertIn("simulation_results", sim_result)
        self.assertIn("var_95", sim_result)
        self.assertIn("cvar_95", sim_result)
        self.assertEqual(len(sim_result["simulation_results"]), simulations_count)

        anomaly_adj = engine._get_anomaly_adjustment()
        self.assertIsInstance(anomaly_adj, float)

        report_id = f"rep_{rand_suffix}"
        loss_limit_val = round(initial_val * 0.1, 2)
        export_res = engine.export_report(report_id=report_id, loss_limit=loss_limit_val)
        
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)
        self.assertEqual(export_res.get("loss_limit"), loss_limit_val)

        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, str, bytes)))

        iterations = random.randint(50, 150)
        scenario_params = {
            "volatility": vol,
            "drift": drift_val,
            "horizon_days": horizon
        }
        
        functional_res = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=initial_val,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(functional_res, dict)
        self.assertEqual(functional_res.get("portfolio_id"), portfolio_id)
        self.assertEqual(functional_res.get("initial_value"), initial_val)
        self.assertEqual(functional_res.get("iterations"), iterations)
        self.assertIn("simulation_id", functional_res)
        self.assertTrue(functional_res["simulation_id"].startswith("sim_"))
        self.assertIn("var_95", functional_res)
        self.assertIn("expected_shortfall", functional_res)

if __name__ == "__main__":
    unittest.main()