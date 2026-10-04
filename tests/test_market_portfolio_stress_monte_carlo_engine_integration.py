import unittest
import uuid
import random

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_audit_compliance_hub
from skills import market_portfolio_stress_monte_carlo_engine


class IntegrationTestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex}"
        self.initial_value = float(random.randint(50000, 500000))
        self.volatility = round(random.uniform(0.1, 0.4), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)

        if hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }

    def test_monte_carlo_stress_engine_integration(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        
        simulations = random.randint(10, 50)
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
        self.assertEqual(len(result["simulation_results"]), simulations)

        report_id = f"rep_{uuid.uuid4().hex}"
        loss_limit = float(random.randint(1000, 10000))
        export_res = engine.export_report(report_id, loss_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)

        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, list, str, bytes)))

        iterations = random.randint(10, 50)
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": horizon_days
        }

        func_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(func_result, dict)
        self.assertEqual(func_result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("simulation_id", func_result)
        self.assertTrue(func_result["simulation_id"].startswith("sim_"))
        self.assertEqual(func_result.get("iterations"), iterations)
        self.assertIn("var_95", func_result)
        self.assertIn("expected_shortfall", func_result)


if __name__ == "__main__":
    unittest.main()