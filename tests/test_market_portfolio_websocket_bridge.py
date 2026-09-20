import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import time

from skills.market_portfolio_websocket_bridge import start_new

class TestMarketPortfolioWebsocketBridge(unittest.TestCase):

    def test_start_new_success_flow(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rand_url = f"https://{uuid.uuid4().hex[:8]}.com/stream"
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(100000, 999999))
        rand_storage = f"{uuid.uuid4().hex}.json"

        mock_storage_instance = MagicMock()
        mock_storage_instance.load_data.return_value = {
            rand_symbol: [round(random.uniform(10.0, 500.0), 2) for _ in range(3)]
        }

        mock_market_parser = MagicMock()
        mock_market_parser.fetch_price.return_value = round(random.uniform(1.0, 1000.0), 2)

        with patch('skills.market_portfolio_websocket_bridge.MarketParser', return_value=mock_market_parser) as p_parser, \
             patch('skills.market_portfolio_websocket_bridge.send_telegram_notification') as p_notify, \
             patch('time.sleep', side_effect=InterruptedError("Stop loop")):
            
            try:
                start_new(
                    symbol=rand_symbol,
                    url=rand_url,
                    telegram_token=rand_token,
                    chat_id=rand_chat_id,
                    storage_file=rand_storage,
                    max_iterations=1
                )
            except InterruptedError:
                pass

        mock_market_parser.fetch_price.assert_called_with(rand_url)
        p_notify.assert_called()
        notif_args = p_notify.call_args[0]
        self.assertEqual(notif_args[0], rand_token)
        self.assertEqual(notif_args[1], rand_chat_id)
        self.assertIn(rand_symbol, notif_args[2])

    def test_start_new_connection_failure_handling(self):
        rand_symbol = f"TOKEN_{uuid.uuid4().hex[:5]}"
        rand_url = f"wss://{uuid.uuid4().hex[:6]}.net/feed"
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(1000, 9999))
        rand_storage = f"{uuid.uuid4().hex}_db.json"

        mock_market_parser = MagicMock()
        mock_market_parser.fetch_price.side_effect = Exception(f"Connection lost {uuid.uuid4().hex[:4]}")

        with patch('skills.market_portfolio_websocket_bridge.MarketParser', return_value=mock_market_parser), \
             patch('skills.market_portfolio_websocket_bridge.send_telegram_notification') as p_notify, \
             patch('time.sleep', side_effect=InterruptedError("Stop loop")):
            
            try:
                start_new(
                    symbol=rand_symbol,
                    url=rand_url,
                    telegram_token=rand_token,
                    chat_id=rand_chat_id,
                    storage_file=rand_storage,
                    max_iterations=1
                )
            except InterruptedError:
                pass

        mock_market_parser.fetch_price.assert_called_once_with(rand_url)
        p_notify.assert_called()
        self.assertIn("Error", p_notify.call_args[0][2])

    def test_start_new_stream_data_payload(self):
        rand_symbol = f"COIN_{uuid.uuid4().hex[:4]}"
        rand_url = f"http://{uuid.uuid4().hex[:6]}.org/api"
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(10000, 99999))
        rand_storage = f"store_{uuid.uuid4().hex}.dat"
        expected_price = round(random.uniform(50.0, 5000.0), 2)

        mock_market_parser = MagicMock()
        mock_market_parser.fetch_price.return_value = expected_price

        captured_messages = []
        def side_effect_notify(token, chat_id, message):
            captured_messages.append(message)
            return True

        with patch('skills.market_portfolio_websocket_bridge.MarketParser', return_value=mock_market_parser), \
             patch('skills.market_portfolio_websocket_bridge.send_telegram_notification', side_effect=side_effect_notify), \
             patch('time.sleep', side_effect=InterruptedError("Stop loop")):
            
            try:
                start_new(
                    symbol=rand_symbol,
                    url=rand_url,
                    telegram_token=rand_token,
                    chat_id=rand_chat_id,
                    storage_file=rand_storage,
                    max_iterations=1
                )
            except InterruptedError:
                pass

        self.assertTrue(len(captured_messages) > 0)
        self.assertIn(str(expected_price), captured_messages[0])
        self.assertIn(rand_symbol, captured_messages[0])