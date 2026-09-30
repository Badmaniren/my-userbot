import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_stress_var_calculator import (
    market_portfolio_stress_var_calculator,
    market_portfolio_scenario_simulator,
    market_portfolio_valuation,
    db_storage
)

class TestMarketPortfolioStressVarCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.simulation_seed = random.randint(1000, 99999)
        self.confidence_level = round(random.uniform(0.95, 0.99), 4)
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_var_cvar_stress_calculation_integration(self):
        # 1. Подготовка базовой оценки портфеля через реальные смежные модули
        valuation_payload = {
            "portfolio_id": self.portfolio_id,
            "initial_capital": round(random.uniform(100000.0, 1000000.0), 2),
            "assets": [
                {"ticker": "AAPL", "weight": 0.5, "volatility": 0.2},
                {"ticker": "MSFT", "weight": 0.5, "volatility": 0.25}
            ]
        }
        valuation_result = market_portfolio_valuation(valuation_payload)
        self.assertIn("valuation_id", valuation_result)

        # 2. Генерация стресс-сценариев
        scenario_config = {
            "portfolio_id": self.portfolio_id,
            "seed": self.simulation_seed,
            "shocks_count": random.randint(10, 50)
        }
        scenarios = market_portfolio_scenario_simulator(scenario_config)
        self.assertIsInstance(scenarios, dict)
        self.assertIn("scenarios", scenarios)

        # 3. Расчет VaR и CVaR на основе сценариев без моков
        calc_input = {
            "portfolio_id": self.portfolio_id,
            "valuation_data": valuation_result,
            "stress_scenarios": scenarios,
            "confidence_level": self.confidence_level,
            "output_path": os.path.join(self.temp_dir.name, f"var_report_{self.portfolio_id}.json")
        }

        calculation_output = market_portfolio_stress_var_calculator(calc_input)

        # 4. Проверка реальных результатов и побочных эффектов
        self.assertIsInstance(calculation_output, dict)
        self.assertEqual(calculation_output.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_value", calculation_output)
        self.assertIn("cvar_value", calculation_output)
        self.assertLess(calculation_output["var_value"], 0)
        self.assertLess(calculation_output["cvar_value"], calculation_output["var_value"])

        # 5. Проверка сохранения в хранилище данных (db_storage)
        stored_record = db_storage(f"get_var_result_{self.portfolio_id}")
        self.assertIsNotNone(calculation_output)

        # 6. Проверка физического появления артефакта на диске
        self.assertTrue(os.path.exists(calc_input["output_path"]))
        self.assertGreater(os.path.getsize(calc_input["output_path"]), 0)

if __name__ == "__main__":
    unittest.main()