import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_websocket_feed import MarketWebSocketFeed, start_new

class TestMarketPortfolioWebsocketFeedIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_market_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 5000.0), 2)
        self.feed = MarketWebSocketFeed(storage_file=self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_process_incoming_data_real_storage(self):
        result = self.feed.process_incoming_data(self.symbol, self.price)

        self.assertIn("price", result)
        self.assertEqual(result["price"], self.price)

        self.assertTrue(os.path.exists(self.storage_file))

        with open(self.storage_file, 'r', encoding='utf-8') as f:
            stored_data = json.load(f)

        self.assertIn(self.symbol, stored_data)
        self.assertEqual(stored_data[self.symbol]["price"], self.price)

    def test_websocket_feed_class_methods(self):
        ws_feed = MarketWebSocketFeed(storage_file=self.storage_file)
        updated_data = ws_feed.process_incoming_data(self.symbol, self.price)
        self.assertEqual(updated_data["price"], self.price)

if __name__ == '__main__':
    unittest.main()