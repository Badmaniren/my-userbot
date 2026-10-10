import unittest
import uuid
import random
from skills.market_portfolio_predictive_var_engine import MarketPortfolioPredictiveVarEngine

class TestMarketPortfolioPredictiveVarEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = MarketPortfolioPredictiveVarEngine()
        self.portfolio_id = str(uuid.uuid4())
        self.portfolio_value = float(random.randint(10000, 1000000))
        self.scenario_params = {
            "scenario_code": f"SCENARIO_{random.randint(100, 999)}",
            "macro_shock": random.uniform(0.01, 0.2),
            "volatility_multiplier": random.uniform(1.0, 2.0)
        }

    def test_predictive_var_calculation_flow(self):
        """
        Интеграционный тест: проверка сквозного прохождения данных через ML-форекастер 
        и Монте-Карло движок без использования моков.
        """
        confidence_level = 0.95
        horizon_days = random.randint(5, 30)
        iterations = random.randint(100, 500)

        # Вызов метода, который объединяет работу ML и Monte Carlo
        result = self.engine.calculate_predictive_stress_var(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.portfolio_value,
            scenario_params=self.scenario_params,
            confidence_level=confidence_level,
            horizon_days=horizon_days,
            iterations=iterations
        )

        # Проверка структуры ответа
        self.assertIn("stress_var", result)
        self.assertIn("conditional_var", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        
        # Проверка логической целостности (VaR не может превышать стоимость портфеля)
        self.assertLessEqual(result["stress_var"], self.portfolio_value)
        self.assertGreaterEqual(result["conditional_var"], result["stress_var"])
        
        # Проверка корректности передачи параметров в метрики
        self.assertEqual(result["simulations_run"], iterations)
        self.assertEqual(result["confidence_level"], confidence_level)

    def test_error_handling_invalid_input(self):
        """
        Проверка обработки исключений при передаче некорректных данных 
        в реальные компоненты системы.
        """
        with self.assertRaises(ValueError):
            self.engine.calculate_predictive_stress_var(
                portfolio_id=self.portfolio_id,
                portfolio_value=-100.0, # Отрицательный баланс
                scenario_params=self.scenario_params
            )

    def test_engine_consistency_with_random_data(self):
        """
        Проверка стабильности движка при генерации случайных идентификаторов 
        и параметров сценария.
        """
        scenario_id = f"TEST_SCENARIO_{uuid.uuid4().hex[:8]}"
        multiplier = random.uniform(0.5, 3.0)
        
        # Проверка работы метода run_standalone_scenario_simulation
        try:
            simulation_result = self.engine.run_standalone_scenario_simulation(
                scenario_id=scenario_id,
                base_multiplier=multiplier
            )
            self.assertIsNotNone(simulation_result)
        except Exception as e:
            self.fail(f"Engine failed to process standalone simulation: {e}")

if __name__ == "__main__":
    unittest.main()