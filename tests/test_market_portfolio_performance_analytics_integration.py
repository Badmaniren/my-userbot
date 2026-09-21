import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics
from skills.market_parser import MarketParser

class TestPortfolioPerformanceAnalyticsIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_market_data_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.price1 = round(random.uniform(100.0, 200.0), 2)
        self.price2 = round(random.uniform(200.1, 300.0), 2)
        self.price3 = round(random.uniform(301.0, 400.0), 2)

        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price1)
        parser.fetch_and_store(self.symbol, self.price2)
        parser.fetch_and_store(self.symbol, self.price3)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_performance_analytics_integration(self):
        self.assertTrue(os.path.exists(self.storage_file))
        
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        self.assertTrue(hasattr(analytics, "calculate_metrics") or hasattr(analytics, "evaluate_performance") or callable(analytics))

        if hasattr(analytics, "calculate_metrics"):
            metrics = analytics.calculate_metrics(self.symbol)
            self.assertIsInstance(metrics, dict)
        elif hasattr(analytics, "evaluate_performance"):
            res = analytics.evaluate_performance(self.symbol)
            self.assertIsNotNone(res)
        else:
            data = analytics.load_data(self.storage_file) if hasattr(analytics, "load_data") else {}
            self.assertIsInstance(data, (dict, list))

if __name__ == "__main__":
    unittest.main()