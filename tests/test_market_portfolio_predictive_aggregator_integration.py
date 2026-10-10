import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_predictive_aggregator import PredictiveAggregator

class TestPredictiveAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_db = f"test_storage_{uuid.uuid4().hex}.json"
        # Инициализация реального файла для имитации работы MarketParser
        with open(self.test_db, 'w') as f:
            json.dump({"data": "initialized"}, f)
        
        self.aggregator = PredictiveAggregator(self.test_db)
        self.symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.url = f"https://api.market.test/{uuid.uuid4().hex}"
        self.shift = random.uniform(0.01, 0.99)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_build_advanced_forecast_integration(self):
        """
        Интеграционный тест: проверяет взаимодействие с MarketParser и PortfolioScenarioSimulator
        без использования моков. Проверяет структуру ответа и корректность обработки данных.
        """
        result = self.aggregator.build_advanced_forecast(self.symbol, self.url, self.shift)

        # Проверка структуры ответа
        self.assertIn("valuation", result)
        self.assertIn("simulation", result)

        # Проверка корректности данных симуляции
        simulation = result["simulation"]
        self.assertEqual(simulation["symbol"], self.symbol)
        self.assertEqual(simulation["shift"], self.shift)
        self.assertIsInstance(simulation["projected_value"], float)

        # Проверка, что данные были обработаны через реальные зависимости
        # Если MarketParser вернул данные, они должны быть в valuation
        self.assertIsInstance(result["valuation"], dict)

    def test_aggregate_market_forecast_alias(self):
        """
        Проверка работы функции-алиаса aggregate_market_forecast
        """
        from skills.market_portfolio_predictive_aggregator import aggregate_market_forecast
        
        result = aggregate_market_forecast(self.test_db, self.symbol, self.url, self.shift)
        
        self.assertEqual(result["simulation"]["symbol"], self.symbol)
        self.assertEqual(result["simulation"]["shift"], self.shift)

if __name__ == '__main__':
    unittest.main()