import unittest
import os
import uuid
import random
from skills.telegram_alert import TelegramAlertService
from skills.market_parser import MarketParser
from skills.db_storage import DatabaseStorage

class TestTelegramAlertIntegration(unittest.TestCase):

    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.db_filename = f"test_db_{self.test_id}.json"
        self.test_symbol = f"COIN_{self.test_id}"
        self.test_url = f"https://example.com/price/{self.test_id}"
        self.threshold_price = round(random.uniform(100.0, 1000.0), 2)
        self.market_price = round(self.threshold_price + random.uniform(10.0, 50.0), 2)

        self.db = DatabaseStorage(self.db_filename)
        self.parser = MarketParser(self.db_filename)
        self.alert_service = TelegramAlertService(db_storage=self.db, market_parser=self.parser)

    def tearDown(self):
        if os.path.exists(self.db_filename):
            os.remove(self.db_filename)

    def test_alert_threshold_integration(self):
        self.parser.fetch_and_store(self.test_symbol, self.market_price)
        
        notification_result = self.alert_service.check_and_alert(
            symbol=self.test_symbol, 
            threshold=self.threshold_price, 
            chat_id=f"chat_{self.test_id}"
        )
        
        self.assertTrue(notification_result)
        
        loaded_data = self.db.load_data(self.db_filename)
        self.assertIn(self.test_symbol, loaded_data)

if __name__ == '__main__':
    unittest.main()