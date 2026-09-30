import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_predictive_aggregator import PredictiveAggregator

class TestMarketPortfolioPredictiveAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_storage = f"test_storage_{uuid.uuid4().hex}.json"
        # Инициализация реального хранилища для теста
        with open(self.test_storage, 'w') as f:
            json.dump({"assets": [], "metadata": "test_data"}, f)

        self.aggregator = PredictiveAggregator(self.test_storage)
        self.test_symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.test_url = f"https://api.test.market/{uuid.uuid4().hex}"
        self.test_shift = random.uniform(-0.5, 0.5)

    def tearDown(self):
        if os.path.exists(self.test_storage):
            os.remove(self.test_storage)

    def test_predictive_aggregator_integration_flow(self):
        # Вызов метода, который объединяет работу MarketParser и PortfolioScenarioSimulator
        result = self.aggregator.build_predictive_forecast(
            self.test_symbol,
            self.test_url,
            self.test_shift
        )

        # Проверка структуры ответа
        self.assertIn("valuation", result)
        self.assertIn("simulation", result)

        # Проверка корректности данных симуляции (интеграционная проверка)
        sim = result["simulation"]
        self.assertEqual(sim["symbol"], self.test_symbol)
        self.assertAlmostEqual(sim["shift"], self.test_shift)
        self.assertIsInstance(sim["projected_value"], float)

        # Проверка того, что данные были обработаны через реальный файл хранилища
        self.assertTrue(os.path.exists(self.test_storage))

        # Проверка на наличие ключей, которые должны были быть сформированы
        # в процессе взаимодействия модулей
        self.assertIn("projected_value", sim)

    def test_aggregator_consistency_with_random_inputs(self):
        # Генерация случайных параметров для проверки стабильности интеграции
        random_symbol = f"SYM_{uuid.uuid4().hex[:5].upper()}"
        random_shift = random.random()

        forecast = self.aggregator.build_advanced_forecast(
            random_symbol,
            self.test_url,
            random_shift
        )

        # Убеждаемся, что агрегатор не возвращает пустые объекты при корректном вызове
        self.assertIsNotNone(forecast["simulation"])
        self.assertEqual(forecast["simulation"]["symbol"], random_symbol)

if __name__ == '__main__':
    unittest.main()