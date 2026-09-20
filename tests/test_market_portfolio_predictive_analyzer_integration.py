import unittest
import os
import uuid
import random
from skills.market_portfolio_predictive_analyzer import PredictiveAnalyzer
from skills.market_portfolio_collector_agent import MarketParser
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator

class TestMarketPortfolioPredictiveAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.storage_file = f"test_storage_{self.test_id}.json"
        self.symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.price = random.uniform(10.0, 500.0)

        # Инициализация зависимых компонентов для подготовки данных
        self.collector = MarketParser(self.storage_file)
        self.simulator = PortfolioScenarioSimulator(self.storage_file)

        # Подготовка начальных данных
        self.collector.fetch_and_store(self.symbol, self.price)

        # Инициализация тестируемого модуля
        self.analyzer = PredictiveAnalyzer(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_predictive_analysis_pipeline_integration(self):
        # Генерируем случайный сценарий для проверки интеграции
        shift = random.uniform(-0.2, 0.2)

        # Вызов тестируемого модуля, который внутри использует collector и simulator
        result = self.analyzer.analyze_and_predict(self.symbol, shift)

        # Проверка структуры ответа
        self.assertIsInstance(result, dict)
        self.assertIn('original_price', result)
        self.assertIn('predicted_value', result)
        self.assertIn('status', result)

        # Проверка корректности данных (интеграция с симулятором)
        expected_prediction = self.price * (1 + shift)
        self.assertAlmostEqual(result['predicted_value'], expected_prediction, places=2)

        # Проверка, что данные были корректно считаны из хранилища (интеграция с collector)
        self.assertEqual(result['symbol'], self.symbol)

        # Проверка записи состояния (side-effect)
        self.assertTrue(os.path.exists(self.storage_file))

        # Проверка целостности данных через повторное чтение
        data = self.collector.load_data(self.storage_file)
        self.assertIsNotNone(data)

    def test_stress_scenario_integration(self):
        # Проверка интеграции с методом run_stress_test симулятора
        shifts = [random.uniform(-0.1, 0.1) for _ in range(3)]

        report = self.analyzer.run_comprehensive_forecast(self.symbol, shifts)

        self.assertIsInstance(report, list)
        self.assertEqual(len(report), len(shifts))

        # Проверка, что каждый элемент отчета содержит данные, полученные из симулятора
        for entry in report:
            self.assertIn('scenario_shift', entry)
            self.assertIn('projected_price', entry)

if __name__ == '__main__':
    unittest.main()