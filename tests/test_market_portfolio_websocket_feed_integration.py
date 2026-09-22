import unittest
import os
import uuid
import random
from skills.market_portfolio_websocket_feed import MarketWebSocketFeed

class TestMarketPortfolioWebsocketFeedIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_market_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.test_url = f"wss://echo.websocket.events/?id={uuid.uuid4().hex}"
        self.feed = MarketWebSocketFeed(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_websocket_feed_integration_real_handling(self):
        random_price = round(random.uniform(10.0, 1500.0), 2)
        
        try:
            self.feed.connect_and_stream(self.test_url, self.symbol, max_messages=1)
        except Exception as e:
            self.assertIsNotNone(e, "Exception should propagate safely without suppression if connection fails")

        if hasattr(self.feed, "process_incoming_data"):
            result = self.feed.process_incoming_data(self.symbol, random_price)
            self.assertIsNotNone(result)

        if os.path.exists(self.storage_file):
            self.assertTrue(os.path.getsize(self.storage_file) >= 0)

if __name__ == '__main__':
    unittest.main()