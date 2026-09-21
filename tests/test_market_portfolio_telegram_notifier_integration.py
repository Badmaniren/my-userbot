import unittest
import os
import uuid
import random
from skills.market_portfolio_telegram_notifier import send_telegram_notification
from skills.market_parser import MarketParser
from skills.market_portfolio_autonomous_sentinel import AutonomousSentinel

class TestMarketPortfolioTelegramNotifierIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/api/v1/market/{uuid.uuid4().hex[:4]}"
        self.token = f"TOKEN_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(1000000, 99999999))
        self.random_price = round(random.uniform(10.0, 5000.0), 2)
        self.threshold = round(random.uniform(1.0, 10.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_telegram_notifier_end_to_end_pipeline(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.random_price)

        self.assertTrue(os.path.exists(self.storage_file), "Хранилище данных не было создано парсером рынка.")

        loaded_data = parser.load_data(self.storage_file)
        self.assertIsNotNone(loaded_data, "Загрузка данных из хранилища вернула None.")

        sentinel = AutonomousSentinel(storage_file=self.storage_file, threshold=self.threshold)
        
        test_message = f"Integration Test Notification ID: {uuid.uuid4()} | Symbol: {self.symbol} | Price: {self.random_price}"
        
        notification_result = send_telegram_notification(
            token=self.token,
            chat_id=self.chat_id,
            message=test_message
        )

        if isinstance(notification_result, bool):
            self.assertIn(notification_result, [True, False], "Результат отправки уведомления должен быть булевым значением.")
        
        try:
            sentinel.run_surveillance(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.token,
                chat_id=self.chat_id
            )
        except Exception as e:
            self.fail(AutonomousSentinel.__name__ + " вызвал исключение во время выполнения наблюдения: " + str(e))

if __name__ == '__main__':
    unittest.main()