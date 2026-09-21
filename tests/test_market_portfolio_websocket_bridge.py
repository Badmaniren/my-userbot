import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import time
from skills.market_portfolio_websocket_bridge import start_new, MarketPortfolioWebsocketBridge

class TestMarketPortfolioWebsocketBridgeStartNew(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex[:6]}"
        self.telegram_token = f"token_{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        self.max_iterations = random.randint(1, 3)

    @patch('skills.market_portfolio_websocket_bridge.MarketParser')
    @patch('skills.market_portfolio_websocket_bridge.send_telegram_notification')
    @patch('time.sleep', return_value=None)
    def test_start_new_success_flow(self, mock_sleep, mock_send_telegram, mock_market_parser_class):
        mock_parser_instance = mock_market_parser_class.return_value
        expected_price = round(random.uniform(10.0, 1000.0), 2)
        mock_parser_instance.fetch_price.return_value = expected_price
        mock_send_telegram.return_value = True

        start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            max_iterations=self.max_iterations
        )

        mock_market_parser_class.assert_called_once_with(self.storage_file)
        self.assertEqual(mock_parser_instance.fetch_price.call_count, self.max_iterations)
        mock_parser_instance.fetch_price.assert_with = (self.url,)

        self.assertEqual(mock_send_telegram.call_count, self.max_iterations)
        expected_message = f"Symbol: {self.symbol}, Price: {expected_price}"
        for call in mock_send_telegram.call_args_list:
            args, _ = call
            self.assertEqual(args[0], self.telegram_token)
            self.assertEqual(args[1], self.chat_id)
            self.assertEqual(args[2], expected_message)

    @patch('skills.market_portfolio_websocket_bridge.MarketParser')
    @patch('skills.market_portfolio_websocket_bridge.send_telegram_notification')
    @patch('time.sleep', return_value=None)
    def test_start_new_exception_flow(self, mock_sleep, mock_send_telegram, mock_market_parser_class):
        mock_parser_instance = mock_market_parser_class.return_value
        error_message = f"Network failure {uuid.uuid4().hex[:4]}"
        mock_parser_instance.fetch_price.side_effect = Exception(error_message)
        mock_send_telegram.return_value = True

        start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            max_iterations=self.max_iterations
        )

        mock_market_parser_class.assert_called_once_with(self.storage_file)
        self.assertEqual(mock_parser_instance.fetch_price.call_count, self.max_iterations)

        self.assertEqual(mock_send_telegram.call_count, self.max_iterations)
        expected_error_message = f"Error: {error_message}"
        for call in mock_send_telegram.call_args_list:
            args, _ = call
            self.assertEqual(args[0], self.telegram_token)
            self.assertEqual(args[1], self.chat_id)
            self.assertEqual(args[2], expected_error_message)

    @patch('skills.market_portfolio_websocket_bridge.MarketParser')
    def test_websocket_bridge_class_emulate_connection(self, mock_market_parser_class):
        bridge = MarketPortfolioWebsocketBridge(self.storage_file)
        result = bridge.emulate_connection()
        self.assertTrue(result)

    @patch('skills.market_portfolio_websocket_bridge.MarketParser')
    def test_websocket_bridge_stream_portfolio_updates(self, mock_market_parser_class):
        mock_parser_instance = mock_market_parser_class.return_value
        random_price = round(random.uniform(50.0, 500.0), 2)
        mock_parser_instance.load_data.return_value = {
            self.symbol: [random_price]
        }

        bridge = MarketPortfolioWebsocketBridge(self.storage_file)
        stream_data = bridge.stream_portfolio_updates(self.symbol)

        expected_string = f"Stream update -> Symbol: {self.symbol}, Price: {random_price}"
        self.assertEqual(stream_data, expected_string)
        mock_parser_instance.load_data.assert_called_once_with(self.storage_file)

    @patch('skills.market_portfolio_websocket_bridge.MarketParser')
    def test_websocket_bridge_stream_portfolio_updates_empty(self, mock_market_parser_class):
        mock_parser_instance = mock_market_parser_class.return_value
        mock_parser_instance.load_data.return_value = {}

        bridge = MarketPortfolioWebsocketBridge(self.storage_file)
        stream_data = bridge.stream_portfolio_updates(self.symbol)

        expected_string = f"Stream update -> Symbol: {self.symbol}, Price: 0.0"
        self.assertEqual(stream_data, expected_string)
        mock_parser_instance.load_data.assert_called_once_with(self.storage_file)