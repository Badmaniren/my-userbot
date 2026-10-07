import unittest
import uuid
import random

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_audit_compliance_hub
from skills import market_portfolio_stress_audit_visualizer
from skills.market_portfolio_stress_monte_carlo_engine import MonteCarloStressEngine, run_monte_carlo_stress_test


class TestIntegrationMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.report_id = f"rep_{uuid.uuid4().hex[:8]}"
        self.initial_value = float(random.randint(50000, 500000))
        self.simulations = random.randint(10, 100)
        self.horizon_days = random.randint(1, 30)
        
        if hasattr(db_storage, "_in_memory_db") and isinstance(db_storage._in_memory_db, dict):
            db_storage._in_memory_db[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": random.uniform(0.1, 0.4),
                "drift": random.uniform(-0.05, 0.05)
            }

    def test_monte_carlo_engine_class_integration(self):
        engine = MonteCarloStressEngine()
        
        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=self.simulations,
            horizon_days=self.horizon_days
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        
        self.assertEqual(len(result["simulation_results"]), self.simulations)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["cvar_95"], float)

        anomaly_adj = engine._get_anomaly_adjustment()
        self.assertIsInstance(anomaly_adj, float)

        export_res = engine.export_report(report_id=self.report_id, loss_limit=1000.0)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), self.report_id)

        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, list, str, bytes)))

    def test_run_monte_carlo_stress_test_function_integration(self):
        scenario_params = {
            "volatility": random.uniform(0.15, 0.35),
            "drift": random.uniform(-0.02, 0.02),
            "horizon_days": random.randint(1, 15)
        }
        
        result = run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=self.simulations
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("initial_value"), self.initial_value)
        self.assertEqual(result.get("iterations"), self.simulations)
        self.assertIn("simulation_id", result)
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()