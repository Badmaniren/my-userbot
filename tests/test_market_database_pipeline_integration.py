import unittest
import os
import uuid
import random
from skills.market_database_pipeline import run_market_database_pipeline

class TestMarketDatabasePipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_market_db_{uuid.uuid4().hex}.json"
        self.test_url = f"https://example.com/market/{uuid.uuid4().hex}"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.expected_price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_pipeline_integration_real_execution(self):
        result = run_market_database_pipeline(
            storage_file=self.storage_file,
            url=self.test_url,
            symbol=self.symbol,
            price=self.expected_price
        )

        self.assertTrue(
            os.path.exists(self.storage_file),
            "Пайплайн должен физически создать файл базы данных."
        )

        self.assertIsNotNone(
            result,
            "Пайплайн должен возвращать результат выполнения."
        )

if __name__ == "__main__":
    unittest.main()