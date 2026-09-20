import unittest
import os
import uuid
import random
from skills.db_storage import MarketParser


class TestMarketParserIntegration(unittest.TestCase):
    def setUp(self):
        self.db_filename = f"test_market_{uuid.uuid4().hex}.db"
        self.parser = MarketParser(storage_file=self.db_filename)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.db_filename):
            os.remove(self.db_filename)

    def test_fetch_and_store_and_load_data_integration(self):
        self.parser.fetch_and_store(self.symbol, self.price)
        
        self.assertTrue(os.path.exists(self.db_filename), "Файл базы данных должен быть создан после сохранения.")
        
        loaded_data = self.parser.load_data(self.db_filename)
        
        self.assertIsInstance(loaded_data, list)
        self.assertGreater(len(loaded_data), 0, "Загруженные данные не должны быть пустыми.")
        
        expected_entry = f"{self.symbol},{self.price}\n"
        self.assertIn(expected_entry, loaded_data, "Сохраненные данные должны корректно читаться из базы.")


if __name__ == '__main__':
    unittest.main()