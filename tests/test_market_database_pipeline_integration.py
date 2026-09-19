import unittest
import os
import uuid
import random
from skills.market_database_pipeline import MarketDatabasePipeline
from skills.market_parser import MarketParser
from skills.db_storage import DbStorage

class TestMarketDatabasePipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_filename = f"test_market_data_{uuid.uuid4()}.json"
        self.pipeline = MarketDatabasePipeline(storage_file=self.test_filename)

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_pipeline_integration_flow(self):
        random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        random_price = round(random.uniform(10.0, 5000.0), 2)
        random_url = f"https://example.com/market/{uuid.uuid4()}"

        result = self.pipeline.process_and_store(symbol=random_symbol, price=random_price, url=random_url)

        self.assertTrue(result, "Конвейер должен успешно обработать и сохранить данные")
        self.assertTrue(os.path.exists(self.test_filename), "Файл базы данных должен быть создан в результате работы конвейера")

        loaded_data = self.pipeline.storage.load_data(self.test_filename)
        
        self.assertIsNotNone(loaded_data, "Загруженные данные не должны быть None")
        
        found = False
        for record in loaded_data:
            if record.get("symbol") == random_symbol and record.get("price") == random_price:
                found = True
                break

        self.assertTrue(found, f"Случайные данные (символ: {random_symbol}, цена: {random_price}) должны быть найдены в хранилище")

if __name__ == "__main__":
    unittest.main()