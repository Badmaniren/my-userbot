import unittest
import os
import uuid
import random
from skills.market_database_pipeline import MarketDatabasePipeline

class TestMarketDatabasePipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_uuid = str(uuid.uuid4())
        self.storage_file = f"test_db_{self.test_uuid}.json"
        self.pipeline = MarketDatabasePipeline(storage_file=self.storage_file)
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_pipeline_storage_integration(self):
        result = self.pipeline.run_pipeline(symbol=self.symbol, price=self.price)
        self.assertTrue(result)

        stored_data = self.pipeline.get_stored_data(self.storage_file)
        self.assertIsInstance(stored_data, list)

        found = False
        for item in stored_data:
            if isinstance(item, dict) and item.get("symbol") == self.symbol:
                self.assertEqual(float(item.get("price")), self.price)
                found = True
                break
            elif isinstance(item, (list, tuple)) and len(item) >= 2 and item[0] == self.symbol:
                self.assertEqual(float(item[1]), self.price)
                found = True
                break

        self.assertTrue(found, f"Символ {self.symbol} с ценой {self.price} не найден в хранилище {self.storage_file}")

if __name__ == "__main__":
    unittest.main()