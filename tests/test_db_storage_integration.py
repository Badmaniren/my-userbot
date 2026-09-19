import unittest
import os
import uuid
import random
from skills.db_storage import MarketParser

class TestMarketParserIntegration(unittest.TestCase):
    
    def setUp(self):
        self.db_filename = f"test_market_data_{uuid.uuid4().hex}.db"
        self.parser = MarketParser(storage_file=self.db_filename)
        self.test_symbol = f"BTC_{uuid.uuid4().hex[:6].upper()}"
        self.test_price = round(random.uniform(10000.0, 100000.0), 2)
        
    def tearDown(self):
        if os.path.exists(self.db_filename):
            os.remove(self.db_filename)
            
    def test_fetch_and_store_integration(self):
        self.parser.fetch_and_store(self.test_symbol, self.test_price)
        
        self.assertTrue(os.path.exists(self.db_filename), "Файл базы данных не был создан.")
        
        loaded_data = self.parser.load_data(self.db_filename)
        
        self.assertIsNotNone(loaded_data, "Метод load_data вернул None.")
        
        found = False
        for row in loaded_data:
            if self.test_symbol in str(row) and str(self.test_price) in str(row):
                found = True
                break
                
        self.assertTrue(found, f"Сохраненные данные для символа {self.test_symbol} с ценой {self.test_price} не найдены в базе данных.")

if __name__ == '__main__':
    unittest.main()