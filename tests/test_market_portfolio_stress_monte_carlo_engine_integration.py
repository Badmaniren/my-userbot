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
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.4), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        self.simulations = random.randint(50, 200)
        self.horizon_days = random.randint(5, 30)
        self.loss_limit = round(self.initial_value * 0.1, 2)

        if not hasattr(db_storage, "_in_memory_db"):
            setattr(db_storage, "_in_memory_db", {})
        
        db_storage._in_memory_db[self.portfolio_id] = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

    def test_monte_carlo_stress_engine_integration(self):
        engine = MonteCarloStressEngine()

        simulation_result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=self.simulations,
            horizon_days=self.horizon_days
        )

        self.assertIsInstance(simulation_result, dict)
        self.assertEqual(simulation_result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", simulation_result)
        self.assertIn("var_95", simulation_result)
        self.assertIn("cvar_95", simulation_result)
        self.assertEqual(len(simulation_result["simulation_results"]), self.simulations)

        export_result = engine.export_report(
            report_id=self.report_id,
            loss_limit=self.loss_limit
        )
        self.assertIsInstance(export_result, dict)
        self.assertEqual(export_result.get("report_id"), self.report_id)
        self.assertEqual(float(export_result.get("loss_limit")), float(self.loss_limit))

        stream_result = engine.consume_stream()
        self.assertTrue(stream_ingested := (stream_result is None or isinstance(stream_result, (dict, list, str, bytes))))

    def test_run_monte_carlo_stress_test_integration(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }

        stress_result = run_monte_carlo_stress_test(
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
        self.assertTrue(stress_result["simulation_id"].startswith("sim_"))
        self.assertIn("var_95", stress_result)
        self.assertIn("expected_shortfall", stress_result)


if __name__ == "__main__":
    unittest.main()