import unittest
import uuid
import random
from skills import db_storage
from skills import market_portfolio_stress_monte_carlo_engine

class TestMonteCarloStressEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        self.portfolio_id = f"test_port_{uuid.uuid4().hex}"
        self.initial_value = float(random.randint(10000, 500000))

        # Инициализация реального хранилища данных
        if hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": 0.15,
                "drift": 0.02
            }

    def test_run_simulation_integration(self):
        simulations = 100
        horizon = 30

        result = self.engine.run_simulation(self.portfolio_id, simulations, horizon)

        # Проверка контракта возвращаемых данных
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertEqual(len(result["simulation_results"]), simulations)
        self.assertIsInstance(result["var_95"], float)
        self.assertGreaterEqual(result["var_95"], 0.0)

    def test_run_monte_carlo_stress_test_functional(self):
        portfolio_id = f"stress_test_{uuid.uuid4().hex}"
        value = float(random.randint(1000, 10000))
        params = {
            "volatility": 0.25,
            "drift": 0.01,
            "horizon_days": 10
        }
        iterations = 50

        result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id, value, params, iterations
        )

        # Проверка генерации уникального ID симуляции
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["iterations"], iterations)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)

    def test_export_report_contract(self):
        report_id = f"rep_{uuid.uuid4().hex}"
        loss_limit = float(random.randint(100, 1000))

        # Проверка вызова модуля экспорта без заглушек
        response = self.engine.export_report(report_id, loss_limit)

        self.assertIsInstance(response, dict)
        self.assertEqual(response.get("report_id"), report_id)
        self.assertEqual(response.get("loss_limit"), loss_limit)

if __name__ == "__main__":
    unittest.main()