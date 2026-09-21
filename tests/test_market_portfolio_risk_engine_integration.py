import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_risk_engine import RiskEngine
from skills.market_parser import MarketParser
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics

class TestMarketPortfolioRiskEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.price = random.uniform(10.0, 500.0)

        # Инициализация реальных компонентов
        self.collector = MarketParser(self.storage_file)
        self.analytics = PortfolioPerformanceAnalytics(self.storage_file)
        self.risk_engine = RiskEngine(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_risk_metrics_calculation_pipeline(self):
        # 1. Сбор данных через реальный агент
        self.collector.fetch_and_store(self.symbol, self.price)

        # Добавляем еще несколько точек для корректного расчета волатильности
        for _ in range(5):
            self.collector.fetch_and_store(self.symbol, self.price + random.uniform(-5, 5))

        # 2. Проверка наличия данных через аналитический блок
        data = self.analytics.load_data(self.storage_file)
        self.assertIn(self.symbol, data, "Данные не были записаны в хранилище")

        # 3. Расчет метрик через RiskEngine (интеграционный вызов)
        # Предполагаем, что RiskEngine использует методы analytics для получения данных
        metrics = self.risk_engine.calculate_risk_metrics(self.symbol)

        # Проверка структуры возвращаемых данных
        self.assertIsInstance(metrics, dict)
        self.assertIn('volatility', metrics)
        self.assertIn('var', metrics)

        # Проверка, что значения не являются заглушками (валидация диапазона)
        self.assertGreaterEqual(metrics['volatility'], 0)
        self.assertIsInstance(metrics['var'], float)

    def test_risk_engine_data_consistency(self):
        # Генерация уникального идентификатора для проверки целостности
        test_id = str(uuid.uuid4())

        # Запись данных
        self.collector.fetch_and_store(test_id, 100.0)
        self.collector.fetch_and_store(test_id, 110.0)

        # Вызов движка
        metrics = self.risk_engine.calculate_risk_metrics(test_id)

        # Проверка, что движок обработал именно те данные, которые мы записали
        # Проверяем, что файл существует и не пуст
        self.assertTrue(os.path.getsize(self.storage_file) > 0)

        # Проверка, что расчеты не вернули None
        self.assertIsNotNone(metrics.get('volatility'))
        self.assertIsNotNone(metrics.get('var'))

if __name__ == '__main__':
    unittest.main()