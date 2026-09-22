import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json
import os

from skills.market_portfolio_websocket_feed import MarketPortfolioWebsocketFeed

class TestMarketPortfolioWebsocketFeed(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.ws_url = f"wss://{uuid.uuid4().hex}.market.feed/ws"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.feed = MarketPortfolioWebsocketFeed(self.storage_file, self.ws_url)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_init_sets_attributes(self):
        custom_storage = f"{uuid.uuid4().hex}.json"
        custom_url = f"wss://{uuid.uuid4().hex}.stream/socket"
        feed_instance = MarketPortfolioWebsocketFeed(custom_storage, custom_url)
        self.assertEqual(feed_instance.storage_file, custom_storage)
        self.assertEqual(feed_instance.ws_url, custom_url)
        self.assertFalse(feed_instance.is_running)

    def test_connect_and_stream_success(self):
        random_price = round(random.uniform(10.0, 5000.0), 2)
        mock_ws_instance = MagicMock()
        mock_ws_instance.__enter__.return_value = mock_ws_instance

        mock_payload = json.dumps({"symbol": self.symbol, "price": random_price})
        mock_ws_instance.recv.side_effect = [mock_payload, Exception(uuid.uuid4().hex)]

        with patch('websockets.sync.client.connect', return_value=mock_ws_instance) as mock_connect:
            ticks = []
            for tick in self.feed.connect_and_stream(self.symbol, max_ticks=1):
                ticks.append(tick)

            mock_connect.assert_called_once_with(self.ws_url)
            self.assertEqual(len(ticks), 1)
            self.assertEqual(ticks[0]['symbol'], self.symbol)
            self.assertEqual(ticks[0]['price'], random_price)

    def test_connect_and_stream_handles_connection_error(self):
        error_message = uuid.uuid4().hex
        with patch('websockets.sync.client.connect', side_effect=Exception(error_message)) as mock_connect:
            ticks = list(self.feed.connect_and_stream(self.symbol, max_ticks=5))
            mock_connect.assert_called_once()
            self.assertEqual(len(ticks), 0)

    def test_simulate_tick_stream_generation(self):
        count = random.randint(3, 8)
        ticks = list(self.feed.simulate_tick_stream(self.symbol, count=count))
        self.assertEqual(len(ticks), count)
        for tick in ticks:
            self.assertEqual(tick['symbol'], self.symbol)
            self.assertIn('price', tick)
            self.assertIn('timestamp', tick)
            self.assertGreater(tick['price'], 0.0)

    def test_broadcast_tick_to_storage(self):
        random_price = round(random.uniform(50.0, 1500.0), 2)
        tick_data = {
            "symbol": self.symbol,
            "price": random_price,
            "timestamp": uuid.uuid4().hex
        }

        self.feed.broadcast_tick_to_storage(tick_data)

        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol][-1]['price'], random_price)
        self.assertEqual(data[self.symbol][-1]['timestamp'], tick_data['timestamp'])

    def test_get_live_stream_summary_non_existent(self):
        summary = self.feed.get_live_stream_summary(self.symbol)
        self.assertEqual(summary['symbol'], self.symbol)
        self.assertEqual(summary['status'], 'no_data')

    def test_get_live_stream_summary_with_data(self):
        prices = [round(random.uniform(100.0, 200.0), 2) for _ in range(4)]
        stored_ticks = []
        for p in prices:
            stored_ticks.append({
                "symbol": self.symbol,
                "price": p,
                "timestamp": uuid.uuid4().hex
            })

        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump({self.symbol: stored_ticks}, f)

        summary = self.feed.get_live_stream_summary(self.symbol)
        self.assertEqual(summary['symbol'], self.symbol)
        self.assertEqual(summary['total_ticks'], 4)
        self.assertEqual(summary['latest_price'], prices[-1])
        self.assertEqual(summary['min_price'], min(prices))
        self.assertEqual(summary['max_price'], max(prices))

if __name__ == '__main__':
    unittest.main()