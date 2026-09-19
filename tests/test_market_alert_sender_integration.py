import unittest
import os
import uuid
import random
from skills.market_alert_sender import MarketAlertSender
from skills.market_parser import MarketParser
from skills.db_storage import DBStorage

class TestMarketAlertSenderIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.db_filename = f"test_market_data_{self.random_suffix}.json"
        
        self.market_parser = MarketParser(storage_file=self.db_filename)
        self.db_storage = DBStorage()
        
        self.alert_sender = MarketAlertSender(
            parser=self.market_parser,
            storage=self.db_storage
        )
        
        self.test_symbol = f"SYM_{self.random_suffix}"
        self.test_price = round(random.uniform(10.0, 1000.0), 2)
        self.test_threshold = self.test_price - round(random.uniform(1.0, 5.0), 2)

    def tearDown(self):
        if os.path.exists(self.db_filename):
            try:
                os.remove(self.db_filename)
            except OSError:
                pass

    def test_alert_sender_integration_flow(self):
        self.market_parser.fetch_and_store(self.test_symbol, self.test_price)
        
        alert_result = self.alert_sender.check_and_send_alert(
            symbol=self.test_symbol,
            threshold=self.test_threshold,
            storage_file=self.db_filename
        )
        
        self.assertTrue(
            os.path.exists(self.db_filename),
            "Файл базы данных должен существовать после выполнения операций парсинга и проверки."
        )
        
        loaded_data = self.market_parser.load_data(self.db_filename)
        self.assertIn(
            self.test_symbol,
            loaded_data,
            f"Символ {self_symbol} должен присутствовать в загруженных данных из файла."
        )
        
        self.assertIsNotNone(
            alert_result,
            "Интеграционный модуль должен вернуть результат проверки алертов."
        )

if __name__ == "__main__":
    unittest.main()