import unittest
import uuid
import random

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_stress_monte_carlo_engine


class TestMonteCarloStressEngineIntegration(unittest.TestCase):

    def test_end_to_end_monte_carlo_simulation_and_export(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_value = round(random.uniform(50000.0, 500000.0), 2)
        simulations = random.randint(100, 500)
        horizon_days = random.randint(5, 30)
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(initial_value * 0.2, 2)

        if hasattr(db_storage, "_in_memory_db") and isinstance(db_storage._in_memory_db, dict):
            db_storage._in_memory_db[portfolio_id] = {
                "portfolio_id": portfolio_id,
                "initial_value": initial_value,
                "volatility": 0.25,
                "drift": 0.02
            }

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        
        sim_result = engine.run_simulation(
            portfolio_id=portfolio_id,
            simulations=simulations,
            horizon_days=horizon_days
        )

        self.assertIsInstance(sim_result, dict)
        self.assertEqual(sim_result.get("portfolio_id"), portfolio_id)
        self.assertIn("var_95", sim_result)
        self.assertIn("cvar_95", sim_result)
        self.assertIn("simulation_results", sim_result)
        self.assertEqual(len(sim_result["simulation_results"]), simulations)

        export_result = engine.export_report(report_id=report_id, loss_limit=loss_limit)
        self.assertIsInstance(export_result, dict)
        self.assertEqual(export_result.get("report_id"), report_id)
        self.assertEqual(export_result.get("loss_limit"), loss_limit)

        stream_data = engine.consume_stream()
        self.assertTrue(stream_data is None or isinstance(stream_data, (dict, list, str, bytes)))

        iterations = random.randint(100, 300)
        scenario_params = {
            "volatility": round(random.uniform(0.1, 0.4), 2),
            "drift": 0.01,
            "horizon_days": horizon_days
        }

        standalone_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(standalone_result, dict)
        self.assertEqual(standalone_result.get("portfolio_id"), portfolio_id)
        self.assertEqual(standalone_result.get("initial_value"), initial_value)
        self.assertEqual(standalone_result.get("iterations"), iterations)
        self.assertIn("simulation_id", standalone_result)
        self.assertTrue(standalone_result["simulation_id"].startswith("sim_"))
        self.assertIn("var_95", standalone_result)
        self.assertIn("expected_shortfall", standalone_result)


if __name__ == "__main__":
    unittest.main()