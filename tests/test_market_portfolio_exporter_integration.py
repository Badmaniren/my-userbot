import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_exporter import MarketPortfolioExporter
from skills.db_storage import MarketParser

class TestMarketPortfolioExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_data_{self.random_suffix}.json"
        self.export_file = f"test_export_{self.random_suffix}.json"
        self.csv_export_file = f"test_export_{self.random_suffix}.csv"

        self.symbol = f"SYM_{self.random_suffix}"
        self.price = round(random.uniform(10.0, 1000.0), 2)

        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)

        self.exporter = MarketPortfolioExporter(self.storage_file)

    def tearDown(self):
        for f in [self.storage_file, self.export_file, self.csv_export_file]:
            if os.path.exists(f):
                os.remove(f)

    def test_export_json_integration(self):
        result = self.exporter.export_to_json(self.export_file)
        self.assertTrue(os.path.exists(self.export_file))

        with open(self.export_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], self.price)

    def test_export_csv_integration(self):
        result = self.exporter.export_to_csv(self.csv_export_file)
        self.assertTrue(os.path.exists(self.csv_export_file))

        with open(self.csv_export_file, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn(self.symbol, content)
        self.assertIn(str(self.price), content)

if __name__ == '__main__':
    unittest.main()