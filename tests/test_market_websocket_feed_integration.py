import unittest
import os
import uuid
import random
import json
from skills.market_websocket_feed import MarketWebSocketFeed
from skills.market_parser import MarketParser
from skills.market_portfolio_stress_reporter import StressReporter

class TestMarketWebsocketFeedIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.test_price = round(random.uniform(10.0, 500.0), 2)
        self.ws_url = f"wss://stream.example.com/ws/{uuid.uuid4().hex}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_websocket_feed_integration_with_storage_and_parser(self):
        feed = MarketWebSocketFeed(self.storage_file)

        self.assertTrue(hasattr(feed, 'connect_and_stream') or hasattr(feed, 'run_feed') or hasattr(feed, 'process_incoming_quote'),
                        "Модуль MarketWebSocketFeed должен содержать методы обработки потока")

        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.test_price)

        reporter = StressReporter(self.storage_file)
        stream_data = reporter.get_stream_data()

        self.assertIsNotNone(stream_data)

        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, (dict, list))

if __name__ == '__main__':
    unittest.main()