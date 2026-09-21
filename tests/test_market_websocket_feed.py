import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.market_websocket_feed import start_new


class TestMarketWebsocketFeed(unittest.TestCase):

    def setUp(self):
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 99999999))
        self.random_message = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        self.random_url = f"wss://{''.join(random.choices(string.ascii_lowercase, k=8))}.com/ws/{uuid.uuid4().hex[:6]}"

    def test_start_new_success_execution(self):
        mock_websocket = MagicMock()
        mock_websocket.recv.return_value = f'{{"symbol": "BTC", "price": {random.uniform(10000, 50000)}}}'
        
        with patch('skills.market_websocket_feed.websockets.connect', return_value=mock_websocket) as mock_connect, \
             patch('skills.market_websocket_feed.send_telegram_notification', return_value=True) as mock_telegram:
            
            result = start_new(self.random_token, self.random_chat_id, self.random_message)
            
            self.assertTrue(result)
            mock_connect.assert_called_once()
            mock_telegram.assert_called()

    def test_start_new_connection_drop_and_recovery(self):
        mock_websocket = MagicMock()
        mock_websocket.recv.side_effect = [
            ConnectionError("Connection lost"),
            f'{{"status": "reconnected", "id": "{uuid.uuid4().hex}"}}'
        ]

        with patch('skills.market_websocket_feed.websockets.connect', return_value=mock_websocket) as mock_connect, \
             patch('skills.market_websocket_feed.time.sleep', return_value=None):
            
            try:
                result = start_new(self.random_token, self.random_chat_id, self.random_message)
            except Exception:
                result = False

            self.assertFalse(result or isinstance(result, bool))
            self.assertGreaterEqual(mock_connect.call_count, 1)

    def test_start_new_invalid_payload_handling(self):
        garbage_bytes = io.BytesIO(uuid.uuid4().bytes)
        mock_websocket = MagicMock()
        mock_websocket.recv.return_value = garbage_bytes.read().decode('latin1')

        with patch('skills.market_websocket_feed.websockets.connect', return_value=mock_websocket), \
             patch('skills.market_websocket_feed.send_telegram_notification') as mock_telegram:
            
            try:
                start_new(self.random_token, self.random_chat_id, self.random_message)
            except Exception:
                pass
            
            mock_telegram.assert_not_called()


if __name__ == '__main__':
    unittest.main()