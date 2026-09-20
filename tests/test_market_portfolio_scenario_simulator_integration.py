import unittest
import os
import uuid
import random
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_parser import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation

class TestMarketPortfolioScenarioSimulatorIntegration(unittest.TestCase):

    def setUp(self):
        self.random_str = str(uuid.uuid4())[:8]
        self.storage_file = f"test_storage_{self.random_str}.json"
        self.symbol = f"TICK_{self.random_str.upper()}"
        self.initial_price = round(random.uniform(10.0, 500.0), 2)
        
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.initial_pid_value := self.initial_price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_scenario_simulator_integration_with_valuation_and_parser(self):
        # Генерируем случайный процент изменения цены для стресс-теста
        shift_percentage = round(random.uniform(-50.0, 50.0), 2)
        
        # Инициализируем тестируемый модуль симулятора сценариев
        simulator = PortfolioScenarioSimulator(self.storage_file)
        
        # Интеграционная проверка расчетов через оценку портфеля
        valuation = PortfolioValuation(self.storage_file)
        initial_summary = valuation.get_total_summary("http://localhost/mock")
        
        self.assertIsNotNone(initial_summary)

        # Выполняем симуляцию изменения рыночных цен
        simulated_result = simulator.simulate_scenario(self.symbol, shift_percentage)
        
        self.assertIsInstance(simulated_result, dict)
        self.assertIn("symbol", simulated_result)
        self.assertEqual(simulated_result["symbol"], self.symbol)
        
        # Проверяем, что файл хранилища по-прежнему доступен и структура не повреждена
        loaded_data = valuation.load_data(self.storage_file)
        self.assertIn(self.symbol, loaded_data)

if __name__ == "__main__":
    unittest.main()