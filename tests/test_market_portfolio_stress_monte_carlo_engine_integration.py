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
        self.report_id = f"rep_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        
        # Настройка хранилища без моков
        if not hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db = {}
            
        db_storage._in_memory_db[self.portfolio_id] = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

    def test_monte_carlo_engine_simulation_and_export(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        
        simulations_count = random.randint(100, 500)
        horizon = random.randint(5, 30)
        
        # Запуск симуляции (интеграция с db_storage и market_anomaly_detector)
        sim_result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations_count,
            horizon_days=horizon
        )
        
        self.assertEqual(sim_result["portfolio_id"], self.portfolio_id)
        self.assertIn("var_95", sim_result)
        self.assertIn("cvar_95", sim_result)
        self.assertIn("simulation_results", sim_result)
        self.assertEqual(len(sim_result["simulation_results"]), simulations_count)
        
        # Проверка экспорта (интеграция с market_portfolio_data_exporter)
        loss_limit = round(random.uniform(1000.0, 10000.0), 2)
        export_res = engine.export_report(self.report_id, loss_limit)
        
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), self.report_id)
        self.assertEqual(export_res.get("loss_limit"), loss_limit)

        # Проверка функциональной функции генерации стресс-теста
        iterations = random.randint(50, 200)
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": horizon
        }
        
        func_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )
        
        self.assertIn("simulation_id", func_result)
        self.assertTrue(func_result["simulation_id"].startswith("sim_"))
        self.assertEqual(func_result["portfolio_id"], self.portfolio_id)
        self.assertEqual(func_result["initial_value"], self.initial_value)
        self.assertEqual(func_result["iterations"], iterations)
        self.assertIn("var_95", func_result)
        self.assertIn("expected_shortfall", func_result)


if __name__ == "__main__":
    unittest.main()