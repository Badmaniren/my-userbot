import unittest
import uuid
import random

from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_audit_compliance_hub


class IntegrationTestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex}"
        self.initial_value = float(random.randint(50000, 500000))
        self.volatility = round(random.uniform(0.1, 0.4), 2)
        self.drift = round(random.uniform(-0.05, 0.05), 4)

        if hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }

    def test_run_simulation_integration(self):
        simulations_count = random.randint(10, 100)
        horizon = random.randint(5, 30)

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations_count,
            horizon_days=horizon
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)

        sim_results = result.get("simulation_results")
        self.assertEqual(len(sim_results), simulations_count)
        for path in sim_results:
            self.assertEqual(len(path), horizon)

        self.assertIsInstance(result.get("var_95"), float)
        self.assertIsInstance(result.get("cvar_95"), float)

    def test_run_monte_carlo_stress_test_functional(self):
        iterations = random.randint(20, 150)
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": random.randint(1, 15)
        }

        stress_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(stress_result, dict)
        self.assertIn("simulation_id", stress_result)
        self.assertTrue(stress_result.get("simulation_id").startswith("sim_"))
        self.assertEqual(stress_result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(stress_result.get("initial_value"), self.initial_value)
        self.assertEqual(stress_result.get("iterations"), iterations)
        self.assertIsInstance(stress_result.get("var_95"), float)
        self.assertIsInstance(stress_result.get("expected_shortfall"), float)

    def test_export_report_and_consume_stream(self):
        report_id = f"rep_{uuid.uuid4().hex}"
        loss_limit = float(random.randint(1000, 10000))

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        export_res = engine.export_report(report_id, loss_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)
        self.assertEqual(export_res.get("loss_limit"), loss_limit)

        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, list, str, tuple)))


if __name__ == "__main__":
    unittest.main()