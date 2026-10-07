import unittest
import uuid
import random
from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_audit_compliance_hub

class TestIntegrationMonteCarloStressEngine(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.4), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        
        if not hasattr(db_storage, "_in_memory_db"):
            setattr(db_storage, "_in_memory_db", {})
        
        db_storage._in_memory_db[self.portfolio_id] = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

    def test_run_simulation_integration(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        simulations_count = random.randint(50, 200)
        horizon = random.randint(5, 30)
        
        result = engine.run_simulation(self.portfolio_id, simulations_count, horizon)
        
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertEqual(len(result["simulation_results"]), simulations_count)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["cvar_95"], float)
        self.assertGreaterEqual(result["cvar_95"], result["var_95"])

    def test_run_monte_carlo_stress_test_function(self):
        scenario_params = {
            "volatility": round(random.uniform(0.15, 0.35), 4),
            "drift": 0.01,
            "horizon_days": random.randint(1, 10)
        }
        iterations = random.randint(100, 300)
        
        res = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )
        
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["initial_value"], self.initial_value)
        self.assertEqual(res["iterations"], iterations)
        self.assertIn("simulation_id", res)
        self.assertTrue(res["simulation_id"].startswith("sim_"))
        self.assertIsInstance(res["var_95"], float)
        self.assertIsInstance(res["expected_shortfall"], float)

    def test_export_report_and_stream(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        report_id = f"rep_{uuid.uuid4().hex[:6]}"
        loss_limit = round(random.uniform(10000.0, 50000.0), 2)
        
        export_res = engine.export_report(report_id, loss_limit)
        self.assertEqual(export_res.get("report_id"), report_id)
        self.assertEqual(export_res.get("loss_limit"), loss_limit)
        
        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, list, str, bytes)))

if __name__ == "__main__":
    unittest.main()