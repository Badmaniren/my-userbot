import unittest
import os
import uuid
import random
from skills.market_status_analyzer import MarketStatusAnalyzer
from skills.db_storage import db_storage

class TestMarketStatusAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_market_{self.unique_id}.json"

        if isinstance(db_storage, type):
            self.storage_instance = db_storage(self.storage_file)
        elif callable(db_storage):
            try:
                self.storage_instance = db_storage(self.storage_file)
            except TypeError:
                self.storage_instance = db_storage
        else:
            self.storage_instance = db_storage

        self.analyzer = MarketStatusAnalyzer(self.storage_file)
        self.symbol = f"TKN{self.unique_id.upper()}"

        self.prices = [
            round(random.uniform(10.0, 50.0), 2),
            round(random.uniform(50.1, 100.0), 2)
        ]

        if hasattr(self.storage_instance, 'fetch_and_store'):
            for p in self.prices:
                self.storage_instance.fetch_and_store(self.symbol, p)
        elif hasattr(self.storage_instance, 'save_data'):
            data = [{"symbol": self.symbol, "price": p} for p in self.prices]
            self.storage_instance.save_data(data)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_integration_analyze_market_status(self):
        random_url = f"https://example.com/market/{self.symbol.lower()}"

        result = self.analyzer.analyze_market_status(self.symbol, url=random_url)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertIn("current_price", result)
        self.assertIn("trend", result)
        self.assertIn("min", result)
        self.assertIn("max", result)
        self.assertIn("average", result)

        metrics = self.analyzer.compute_base_metrics(self.prices)
        self.assertEqual(result["min"], metrics["min"])
        self.assertEqual(result["max"], metrics["max"])
        self.assertEqual(result["average"], metrics["average"])

if __name__ == '__main__':
    unittest.main()