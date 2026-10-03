import unittest
import uuid
import random

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_stress_monte_carlo_engine


class TestMonteCarloStressEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.4), 2)
        self.drift = round(random.uniform(-0.05, 0.05), 4)

        # Настраиваем хранилище реальными динамическими данными без моков
        if hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }

        self.engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()

    def test_run_simulation_integration(self):
        simulations_count = random.randint(50, 200)
        horizon = random.randint(5, 30)

        result = self.engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations_count,
            horizon_days=horizon
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)

        sim_results = result["simulation_results"]
        self.assertEqual(len(sim_results), simulations_count)
        for path in sim_results:
            self.assertEqual(len(path), horizon)

        self.assertGreaterEqual(result["var_95"], 0.0)
        self.assertGreaterEqual(result["cvar_95"], 0.0)

    def test_export_report_integration(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)

        export_res = self.engine.export_report(report_id, loss_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)
        self.assertEqual(export_res.get("loss_limit"), loss_limit)

    def test_consume_stream_integration(self):
        stream_res = self.engine.consume_stream()
        # Проверяем интеграционный вызов без падений, тип может зависеть от реализации шлюза
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, list, str)))

    def test_run_monte_carlo_stress_test_functional(self):
        iterations = random.randint(50, 150)
        scenario_params = {
            "volatility": round(random.uniform(0.15, 0.35), 2),
            "drift": round(random.uniform(-0.02, 0.02), 4),
            "horizon_days": random.randint(1, 15)
        }

        stress_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(stress_result.get("initial_value"), self.initial_value)
        self.assertEqual(stress_result.get("iterations"), iterations)
        self.assertIn("simulation_id", stress_result)
        self.assertIn("var_95", stress_result)
        self.assertIn("expected_shortfall", stress_result)
        self.assertTrue(stress_result["simulation_id"].startswith("sim_"))


if __name__ == "__main__":
    unittest.main()