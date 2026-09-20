import unittest
import os
import uuid
import random
from skills.market_database_pipeline import run_market_database_pipeline

class TestMarketDatabasePipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_storage"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

        self.unique_id = uuid.uuid4().hex[:8]
        self.storage_file = os.path.join(self.test_dir, f"db_{self.unique_id}.json")

        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.random_price = round(random.uniform(10.0, 1000.0), 2)
        self.test_url = f"http://example.com/market/{self.unique_id}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.test_dir) and not os.listdir(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_market_database_pipeline_real_integration(self):
        result = run_market_database_pipeline(
            url=self.test_url,
            symbol=self.symbol,
            storage_file=self.storage_file
        )

        self.assertTrue(
            os.path.exists(self.storage_file),
            f"Файл хранилища {self.storage_file} не был создан в результате работы пайплайна."
        )

        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(
                self.symbol,
                content,
                f"Сгенерированный символ {self.symbol} отсутствует в файле базы данных."
            )

        self.assertIsNotNone(
            result,
            "Пайплайн должен возвращать результат выполнения операции сохранения."
        )

if __name__ == "__main__":
    unittest.main()