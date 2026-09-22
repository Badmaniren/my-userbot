import unittest
from unittest.mock import patch, MagicMock
import json
import uuid
import random
import os
from skills.market_portfolio_websocket_feed import start_new, MarketWebSocketFeed


class TestMarketPortfolioWebsocketFeed(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.uri = f"ws://localhost:{random.randint(1000, 9999)}/{uuid.uuid4().hex}"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:20]}"
        self.chat_id = str(random.randint(1000000, 99999999))
        self.price = round(random.uniform(1.0, 1000.0), 4)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_start_new_success_flow(self):
        message_data = json.dumps({"price": self.price})

        class DummyWebSocketApp:
            def __init__(self, uri, on_message, on_error):
                self.on_message = on_message
                self.on_error = on_error

            def run_forever(self):
                self.on_message(self, message_data)

        with patch("websocket.WebSocketApp", side_effect=lambda uri, on_message, on_error: DummyWebSocketApp(uri, on_message, on_error)), \
             patch("skills.market_portfolio_websocket_feed.send_telegram_notification") as mock_telegram, \
             patch("skills.market_portfolio_websocket_feed.MarketWebSocketFeed") as mock_feed_cls:

            mock_feed_instance = MagicMock()
            mock_feed_cls.return_value = mock_feed_instance

            result = start_new(self.uri, self.symbol, self.telegram_token, self.chat_id)

            self.assertTrue(result)
            mock_feed_instance.process_incoming_data.assert_called_once_with(self.symbol, self.price)
            mock_telegram.assert_called_once()
            args, _ = mock_telegram.call_args
            self.assertEqual(args[0], self.telegram_token)
            self.assertEqual(args[1], self.chat_id)
            self.assertIn(str(self.price), args[2])
            self.assertIn(self.symbol, args[2])

    def test_start_new_invalid_json(self):
        invalid_message = f"invalid_json_{uuid.uuid4().hex}"

        class DummyWebSocketApp:
            def __init__(self, uri, on_message, on_error):
                self.on_message = on_message
                self.on_error = on_error

            def run_forever(self):
                self.on_message(self, invalid_message)

        with patch("websocket.WebSocketApp", side_effect=lambda uri, on_message, on_error: DummyWebSocketApp(uri, on_message, on_error)), \
             patch("skills.market_portfolio_websocket_feed.send_telegram_notification") as mock_telegram, \
             patch("skills.market_portfolio_websocket_feed.MarketWebSocketFeed") as mock_feed_cls:

            mock_feed_instance = MagicMock()
            mock_feed_cls.return_value = mock_feed_instance

            result = start_new(self.uri, self.symbol, self.telegram_token, self.chat_id)

            self.assertTrue(result)
            mock_feed_instance.process_incoming_data.assert_not_called()
            mock_telegram.assert_not_called()

    def test_start_new_missing_price_key(self):
        message_data = json.dumps({"volume": random.randint(100, 500)})

        class DummyWebSocketApp:
            def __init__(self, uri, on_message, on_error):
                self.on_message = on_message
                self.on_error = on_error

            def run_forever(self):
                self.on_message(self, message_data)

        with patch("websocket.WebSocketApp", side_effect=lambda uri, on_message, on_error: DummyWebSocketApp(uri, on_message, on_error)), \
             patch("skills.market_portfolio_websocket_feed.send_telegram_notification") as mock_telegram, \
             patch("skills.market_portfolio_websocket_feed.MarketWebSocketFeed") as mock_feed_cls:

            mock_feed_instance = MagicMock()
            mock_feed_cls.return_value = mock_feed_instance

            result = start_new(self.uri, self.symbol, self.telegram_token, self.chat_id)

            self.assertTrue(result)
            mock_feed_instance.process_incoming_data.assert_not_called()
            mock_telegram.assert_not_called()

    def test_start_new_websocket_error_propagation(self):
        test_exception = Exception(f"error_{uuid.uuid4().hex}")

        class DummyWebSocketApp:
            def __init__(self, uri, on_message, on_error):
                self.on_message = on_message
                self.on_error = on_error

            def run_forever(self):
                self.on_error(self, test_exception)

        with patch("websocket.WebSocketApp", side_effect=lambda uri, on_message, on_error: DummyWebSocketApp(uri, on_message, on_error)):
            with self.assertRaises(Exception) as ctx:
                start_new(self.uri, self.symbol, self.telegram_token, self.chat_id)
            self.assertEqual(ctx.exception, test_exception)

    def test_market_web_socket_feed_process_incoming_data(self):
        feed = MarketWebSocketFeed(storage_file=self.storage_file)
        result = feed.process_incoming_data(self.symbol, self.price)

        self.assertEqual(result, {"price": self.price})
        self.assertTrue(os.path.exists(self.storage_file))

        with open(self.storage_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        self.assertIn(self.symbol, saved_data)
        self.assertEqual(saved_data[self.symbol]["price"], self.price)


if __name__ == '__main__':
    unittest.main()