import unittest
import os
import sqlite3
import uuid
import random
from skills.db_storage import MarketParser

class TestIntegrationDbStorage(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_market_data_{self.test_id}.db"
        self.parser = MarketParser(storage_file=self.storage_file)
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.price = round(random.uniform(10.0, 500.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_persistence_and_load_flow(self):
        self.parser.fetch_and_store(self.symbol, self.price)
        
        self.assertTrue(os.path.exists(self.storage_file), "Файл базы данных должен быть создан после сохранения.")
        
        loaded_lines = self.parser.load_data(self.storage_file)
        
        self.assertIsInstance(loaded_lines, list)
        self.assertGreater(len(loaded_lines), 0, "Загруженные данные не должны быть пустыми.")
        
        found = False
        expected_str = f"{self.symbol},{self.price}\n"
        for line in loaded_lines:
            if line == expected_str:
                found = True
                break
                
        self.assertTrue(found, f"Сохраненные данные '{expected_str.strip()}' должны корректно считываться через load_data.")

if __name__ == "__main__":
    unittest.main()