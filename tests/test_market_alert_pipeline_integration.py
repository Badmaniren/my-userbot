import unittest
import os
import uuid
import random
from skills.market_alert_pipeline import MarketAlertPipeline
from skills.market_parser import MarketParser
from skills.db_storage import MarketParser as DBStorageMarketParser


class TestMarketAlertPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.test_storage_file = f"test_market_storage_{self.random_suffix}.json"
        
        self.test_symbol = f"SYM_{self.random_suffix}"
        self.test_price = round(random.uniform(10.0, 1000.0), 2)
        self.test_url = f"http://example.com/market/{self.test_symbol.lower()}"

        self.pipeline = MarketAlertPipeline(storage_file=self.test_storage_file)

    def tearDown(self):
        if os.path.exists(self.test_storage_file):
            os.remove(self.test_storage_file)

    def test_pipeline_integration_flow(self):
        result = self.pipeline.process_alert_check(
            symbol=self.test_symbol,
            url=self.test_url,
            threshold_price=self.test_price + 50.0
        )

        self.assertIsInstance(result, dict)
        self.assertIn("alert_triggered", result)
        self.assertIn("current_price", result)

        loaded_data = self.pipeline.db_storage.load_data(self.test_storage_file)
        self.assertIsInstance(loaded_data, (dict, list))


if __name__ == "__main__":
    unittest.main()