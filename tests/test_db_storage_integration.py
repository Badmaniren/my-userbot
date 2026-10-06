import unittest
import os
import uuid
import random
from skills.db_storage import MarketParser


class TestDbStorageIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_data_{self.random_suffix}.db"
        self.parser = MarketParser(storage_file=self.storage_file)
        
    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_fetch_and_store_integration_strict_types(self):
        test_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        test_price = round(random.uniform(10.0, 5000.0), 4)

        self.parser.fetch_and_store(symbol=test_symbol, price=test_price)

        self.assertTrue(os.path.exists(self.storage_file), "Файл базы данных должен быть создан после сохранения.")

        loaded_data = self.parser.load_data(self.storage_file)
        
        self.assertIsInstance(loaded_data, list, "load_data должен возвращать список строк.")
        self.assertGreater(len(loaded_data), 0, "Список загруженных данных не должен быть пустым.")

        found = False
        expected_line = f"{test_symbol},{test_price}\n"
        for line in loaded_data:
            if test_symbol in line and str(test_price) in line:
                found = True
                break

        self.assertTrue(found, f"Записанные данные для символа {test_symbol} с ценой {test_price} должны успешно читаться из хранилища.")

    def test_storage_invalid_structure_handling(self):
        invalid_filename = f"invalid_{self.random_suffix}.txt"
        random_text_content = f"ID-{uuid.uuid4()}:{random.randint(1000, 9999)}\n"
        
        with open(invalid_filename, 'w', encoding='utf-8') as f:
            f.write(random_text_content)

        try:
            data = self.parser.load_data(invalid_filename)
            self.assertIsInstance(data, list)
            self.assertIn(random_text_content, data)
        finally:
            if os.path.exists(invalid_filename):
                os.remove(invalid_filename)


if __name__ == '__main__':
    unittest.main()