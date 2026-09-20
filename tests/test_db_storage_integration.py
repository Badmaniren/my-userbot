import unittest
import os
import uuid
import random
from skills.db_storage import MarketParser

class TestDbStorageIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_market_{uuid.uuid4().hex}.db"
        self.parser = MarketParser(storage_file=self.storage_file)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_fetch_and_store_and_load_data_integration(self):
        self.parser.fetch_and_store(self.symbol, self.price)
        
        self.assertTrue(os.path.exists(self.storage_file), "Файл базы данных должен быть создан после сохранения.")
        
        loaded_data = self.parser.load_data(self.storage_file)
        
        self.assertIsInstance(loaded_data, list)
        self.assertGreater(len(loaded_data), 0, "Загруженные данные не должны быть пустыми.")
        
        expected_line = f"{self.symbol},{self.price}\n"
        self.assertIn(expected_line, loaded_data, "Сохраненные данные должны корректно читаться из базы данных.")

if __name__ == '__main__':
    unittest.main()