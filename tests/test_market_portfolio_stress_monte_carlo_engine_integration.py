import unittest
import uuid
import random
from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage


class TestIntegrationMonteCarloStressEngine(unittest.TestCase):

    def test_monte_carlo_simulation_and_stress_test_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_val = round(random.uniform(50000.0, 500000.0), 2)
        vol = round(random.uniform(0.1, 0.5), 4)
        drift_val = round(random.uniform(-0.05, 0.05), 4)
        sim_count = random.randint(100, 500)
        horizon = random.randint(5, 30)

        in_mem = getattr(db_storage, "_in_memory_db", None)
        if in_mem is None:
            in_mem = {}
            setattr(db_storage, "_in_memory_db", in_mem)
        
        in_mem[portfolio_id] = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_val,
            "volatility": vol,
            "drift": drift_val
        }

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        sim_result = engine.run_simulation(portfolio_id, simulations=sim_count, horizon_days=horizon)

        self.assertIsInstance(sim_result, dict)
        self.assertEqual(sim_result["portfolio_id"], portfolio_id)
        self.assertIn("simulation_results", sim_result)
        self.assertIn("var_95", sim_result)
        self.assertIn("cvar_95", sim_result)
        self.assertGreaterEqual(sim_result["cvar_95"], sim_result["var_95"])

        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 15000.0), 2)
        export_res = engine.export_report(report_id, loss_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)

        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, list, str, bytes)))

        scenario_params = {
            "volatility": vol,
            "drift": drift_val,
            "horizon_days": horizon
        }
        stress_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=initial_val,
            scenario_params=scenario_params,
            iterations=sim_count
        )

        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result["portfolio_id"], portfolio_id)
        self.assertEqual(stress_result["initial_value"], initial_val)
        self.assertIn("simulation_id", stress_result)
        self.assertTrue(stress_result["simulation_id"].startswith("sim_"))
        self.assertGreaterEqual(stress_result["expected_shortfall"], stress_result["var_95"])
        self.assertEqual(stress_result["iterations"], sim_count)


if __name__ == "__main__":
    unittest.main()