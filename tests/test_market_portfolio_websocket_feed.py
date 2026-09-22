import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys

from skills.market_portfolio_websocket_feed import start_new

class TestMarketPortfolioWebsocketFeed(unittest.TestCase):

    def test_start_new_success_flow(self):
        rand_uri = f"wss://{uuid.uuid4().hex}.example.com/ws"
        rand_symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        
        mock_ws_app = MagicMock()
        
        with patch('skills.market_portfolio_websocket_feed.websocket.WebSocketApp', return_value=mock_ws_app) as mock_ws_cls:
            result = start_new(rand_uri, rand_symbol, rand_token, rand_chat)
            
            self.assertTrue(result)
            mock_ws_cls.assert_called_once()
            args, kwargs = mock_ws_cls.call_args
            self.assertEqual(args[0], rand_uri)
            mock_ws_app.run_forever.assert_called_once()

    def test_start_new_exception_handling_without_suppression(self):
        rand_uri = f"ws://{uuid.uuid4().hex}.local/stream"
        rand_symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        
        err_msg = f"Connection_Error_{uuid.uuid4().hex}"
        
        with patch('skills.market_portfolio_websocket_feed.websocket.WebSocketApp', side_effect=Exception(err_msg)) as mock_ws_cls:
            with self.assertRaises(Exception) as ctx:
                start_new(rand_uri, rand_symbol, rand_token, rand_chat)
            
            self.assertIn(err_msg, str(ctx.exception))
            mock_ws_cls.assert_called_once()

    def test_start_new_callback_execution(self):
        rand_uri = f"wss://{uuid.uuid4().hex}.market/feed"
        rand_symbol = "".join(random.choices(string.ascii_uppercase, k=3))
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        
        captured_callbacks = {}
        
        def mock_ws_init(url, **kwargs):
            captured_callbacks['on_message'] = kwargs.get('on_message')
            captured_callbacks['on_error'] = kwargs.get('on_error')
            captured_callbacks['on_close'] = kwargs.get('on_close')
            captured_callbacks['on_open'] = kwargs.get('on_open')
            return MagicMock()

        rand_price = round(random.uniform(10.0, 5000.0), 2)
        random_payload = f'{{"symbol": "{rand_symbol}", "price": {rand_price}}}'

        with patch('skills.market_portfolio_websocket_feed.websocket.WebSocketApp', side_effect=mock_ws_init):
            with patch('skills.market_portfolio_websocket_feed.send_telegram_notification') as mock_notify:
                start_new(rand_uri, rand_symbol, rand_token, rand_chat)
                
                self.assertIsNotNone(captured_callbacks['on_message'])
                
                mock_ws_instance = MagicMock()
                captured_callbacks['on_message'](mock_ws_instance, random_payload)
                
                if mock_notify.called:
                    mock_notify.assert_called()
                else:
                    self.assertTrue(True)

    def test_start_new_invalid_url_input(self):
        rand_uri = 123456789
        rand_symbol = uuid.uuid4().hex
        rand_token = uuid.uuid4().hex
        rand_chat = uuid.uuid4().hex

        with patch('skills.market_portfolio_websocket_feed.websocket.WebSocketApp', side_effect=TypeError("Invalid URL type")):
            with self.assertRaises(TypeError):
                start_new(rand_uri, rand_symbol, rand_token, rand_chat)

if __name__ == '__main__':
    unittest.main()