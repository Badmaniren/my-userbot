import unittest
import os
import uuid
import random
import tempfile

from skills.market_portfolio_websocket_feed import WebSocketFeedProcessor
from skills.market_portfolio_autonomous_sentinel import AutonomousSentinel
from skills.db_storage import MarketParser

class TestMarketPortfolioWebsocketFeedIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/api/market/{uuid.uuid4().hex}"
        self.telegram_token = f"bot_token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.threshold = round(random.uniform(10.0, 100.0), 2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_websocket_feed_triggers_sentinel_and_storage(self):
        initial_price = round(random.uniform(50.0, 150.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=initial_price)

        sentinel = AutonomousSentinel(storage_file=self.storage_file, threshold=self.threshold)
        feed_processor = WebSocketFeedProcessor(storage_file=self.storage_file, sentinel=sentinel)

        live_price = initial_price + self.threshold + round(random.uniform(1.0, 10.0), 2)

        feed_processor.ingest_live_quote(symbol=self.symbol, price=live_price, url=self.url, telegram_token=self.telegram_token, chat_id=self.chat_id)

        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан в процессе интеграционного пайплайна.")

        loaded_data = parser.load_data(self.storage_file)
        self.assertIn(self.symbol, str(loaded_data), f"Символ {self.symbol} должен быть сохранен после обработки websocket-потока.")

if __name__ == '__main__':
    unittest.main()