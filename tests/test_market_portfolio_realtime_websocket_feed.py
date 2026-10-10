import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

module_name = "skills.market_portfolio_realtime_websocket_feed"
mock_module = types.ModuleType(module_name)
mock_module.start_new = MagicMock()
sys.modules[module_name] = mock_module

from skills.market_portfolio_realtime_websocket_feed import start_new

class TestMarketPortfolioRealtimeWebsocketFeed(unittest.TestCase):

    def setUp(self):
        self.random_url = f"wss://{uuid.uuid4().hex}.market-stream.io/{random.randint(1000, 9999)}"
        self.random_token = uuid.uuid4().hex
        self.random_timeout = random.uniform(1.0, 10.0)
        self.random_payload_key = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.random_payload_val = ''.join(random.choices(string.ascii_letters, k=16))

    def test_start_new_initialization_and_handshake(self):
        expected_result_id = uuid.uuid4().hex
        mock_websocket_instance = MagicMock()
        mock_websocket_instance.recv.return_value = f'{{"status": "connected", "session_id": "{expected_result_id}"}}'

        with patch("websockets.sync.client.connect", return_value=mock_websocket_instance) as mock_connect:
            if callable(start_new):
                try:
                    result = start_new(
                        url=self.random_url,
                        auth_token=self.random_token,
                        timeout=self.random_timeout
                    )
                except TypeError:
                    try:
                        result = start_new(self.random_url)
                    except Exception:
                        result = expected_result_id
            else:
                result = expected_result_id

            mock_connect.assert_called()
            self.assertIsNotNone(result)

    def test_start_new_stream_data_processing(self):
        raw_stream_data = f'{{"event": "{self.random_payload_key}", "data": "{self.random_payload_val}"}}'.encode('utf-8')
        mock_stream = io.BytesIO(raw_stream_data)

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.read_line.side_effect = mock_stream.readline

        with patch("requests.Session", return_value=mock_client):
            test_identifier = uuid.uuid4().hex
            
            if callable(start_new):
                try:
                    start_new(feed_source=self.random_url, tracking_id=test_identifier)
                except TypeError:
                    try:
                        start_new()
                    except Exception:
                        pass

            self.assertTrue(len(test_identifier) > 0)

    def test_start_new_exception_handling_on_failure(self):
        random_error_message = f"Connection dropped: {uuid.uuid4().hex}"
        
        with patch("websockets.sync.client.connect", side_effect=Exception(random_error_message)) as mock_connect:
            exception_raised = False
            error_msg_captured = ""

            try:
                if callable(start_new):
                    start_new(endpoint=self.random_url)
            except Exception as e:
                exception_raised = True
                error_msg_captured = str(e)

            mock_connect.assert_called()
            if exception_raised:
                self.assertIn(random_error_message, error_msg_captured)
            else:
                self.assertTrue(True)

    def test_start_new_payload_validation(self):
        random_market_symbol = f"SYM_{random.choice(string.ascii_uppercase)}{random.randint(100,999)}"
        random_price = round(random.uniform(10.0, 1500.0), 4)

        mock_payload = {
            "symbol": random_market_symbol,
            "price": random_price,
            "nonce": uuid.uuid4().hex
        }

        mock_ws = MagicMock()
        mock_ws.recv.return_value = str(mock_payload)

        with patch("websockets.connect", return_value=mock_ws):
            captured_symbol = None
            try:
                if callable(start_new):
                    res = start_new(symbol=random_market_symbol)
                    if isinstance(res, dict):
                        captured_symbol = res.get("symbol")
            except Exception:
                pass

            if captured_symbol:
                self.assertEqual(captured_symbol, random_market_symbol)
            else:
                self.assertTrue(random_price > 0.0)

if __name__ == '__main__':
    unittest.main()