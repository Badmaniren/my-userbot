import unittest
import os
import uuid
import random
from skills.market_alert_analyzer import MarketAlertAnalyzer
from skills.market_parser import MarketParser
from skills.db_storage import load_data

class TestMarketAlertAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.random_suffix}.json"
        self.symbol = f"BTC_{self.random_suffix}"
        self.url = f"https://example.com/price/{self.random_suffix}"
        self.random_price = round(random.uniform(10000.0, 50000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_alert_analyzer_integration_with_real_modules(self):
        parser = MarketParser(storage_file=self.storage_file)

        self.assertTrue(hasattr(parser, 'fetch_and_store'))
        parser.fetch_and_store(symbol=self.symbol, price=self.random_price)

        analyzer = MarketAlertAnalyzer(storage_file=self.storage_file)

        self.assertTrue(hasattr(analyzer, 'analyze_thresholds'))

        threshold = self.random_price - 100.0
        alerts = analyzer.analyze_thresholds(symbol=self.symbol, threshold=threshold)

        self.assertIsInstance(alerts, list)

        stored_data = load_data(self.storage_file)
        self.assertIn(self.symbol, stored_data)

if __name__ == '__main__':
    unittest.main()