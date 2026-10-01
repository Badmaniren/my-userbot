import unittest
import uuid
import random

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_stress_monte_carlo_engine


class TestIntegrationMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        self.simulations = random.randint(100, 500)
        self.horizon_days = random.randint(10, 30)

        if hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }

    def test_monte_carlo_simulation_end_to_end(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        
        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=self.simulations,
            horizon_days=self.horizon_days
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        
        self.assertEqual(len(result["simulation_results"]), self.simulations)
        self.assertGreaterEqual(result["var_95"], 0.0)
        self.assertGreaterEqual(result["cvar_95"], 0.0)

    def test_anomaly_adjustment_integration(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        adjustment = engine._get_anomaly_adjustment()
        self.assertIsInstance(adjustment, float)
        self.assertGreater(adjustment, 0.0)

    def test_export_report_integration(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 10000.0), 2)
        
        export_res = engine.export_report(report_id=report_id, loss_limit=loss_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)
        self.assertEqual(export_res.get("loss_limit"), loss_limit)

    def test_consume_stream_integration(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, list, str, bytes)))

    def test_run_monte_carlo_stress_test_function(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }
        
        stress_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=self.simulations
        )

        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result["portfolio_id"], self.portfolio_id)
        self.assertEqual(stress_result["initial_value"], self.initial_value)
        self.assertEqual(stress_result["iterations"], self.simulations)
        self.assertIn("simulation_id", stress_result)
        self.assertIn("var_95", stress_result)
        self.assertIn("expected_shortfall", stress_result)


if __name__ == "__main__":
    unittest.main()