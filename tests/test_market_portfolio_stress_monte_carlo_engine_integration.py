import unittest
import uuid
import random

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_audit_compliance_hub
from skills import market_portfolio_stress_audit_visualizer
from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = float(random.randint(50000, 500000))
        
        if not hasattr(db_storage, "_in_memory_db"):
            setattr(db_storage, "_in_memory_db", {})
        
        db_storage._in_memory_db[self.portfolio_id] = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": 0.25,
            "drift": 0.02
        }

    def test_run_simulation_integration(self):
        engine = MonteCarloStressEngine()
        simulations = random.randint(100, 500)
        horizon_days = random.randint(5, 30)

        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations,
            horizon_days=horizon_days
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertGreaterEqual(result["cvar_95"], result["var_95"])
        self.assertEqual(len(result["simulation_results"]), simulations)

    def test_run_monte_carlo_stress_test_integration(self):
        iterations = random.randint(100, 400)
        scenario_params = {
            "volatility": round(random.uniform(0.15, 0.45), 2),
            "drift": 0.01,
            "horizon_days": random.randint(1, 15)
        }

        res = run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(res, dict)
        self.assertTrue(res["simulation_id"].startswith("sim_"))
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["iterations"], iterations)
        self.assertGreaterEqual(res["expected_shortfall"], res["var_95"])

    def test_export_report_integration(self):
        engine = MonteCarloStressEngine()
        report_id = f"rep_{uuid.uuid4().hex[:6]}"
        loss_limit = float(random.randint(10000, 50000))

        export_res = engine.export_report(report_id, loss_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)

    def test_consume_stream_integration(self):
        engine = MonteCarloStressEngine()
        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, list, str, bytes)))


if __name__ == "__main__":
    unittest.main()