import unittest
import os
import uuid
import random
from skills.market_portfolio_performance_tracker import PerformanceTracker
from skills.db_storage import MarketParser

class TestMarketPortfolioPerformanceTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_market_data_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.parser = MarketParser(self.storage_file)
        
        self.initial_prices = [round(random.uniform(100.0, 500.0), 2) for _ in range(5)]
        for price in self.initial_prices:
            self.parser.fetch_and_store(self.symbol, price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_performance_tracker_integration_flow(self):
        self.assertTrue(os.path.exists(self.storage_file), "Файл базы данных должен быть создан.")
        
        tracker = PerformanceTracker(self.storage_file)
        self.assertTrue(hasattr(tracker, "calculate_performance"), "Модуль должен содержать метод расчета производительности.")
        
        metrics = tracker.calculate_performance(self.symbol)
        
        self.assertIsInstance(metrics, dict, "Результат метрик должен быть словарем.")
        self.assertIn("total_return", metrics, "Метрики должны содержать общую доходность.")
        self.assertIn("volatility", metrics, "Метрики должны содержать волатильность.")
        
        random_extra_price = round(random.uniform(500.1, 1000.0), 2)
        self.parser.fetch_and_store(self.symbol, random_extra_price)
        
        updated_metrics = tracker.calculate_performance(self.symbol)
        self.assertNotEqual(
            metrics.get("total_return"), 
            updated_metrics.get("total_return"), 
            "Доходность должна измениться после добавления новых реальных данных."
        )

if __name__ == "__main__":
    unittest.main()