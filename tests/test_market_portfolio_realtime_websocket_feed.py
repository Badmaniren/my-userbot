import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import sys
import types

websockets_mock = types.ModuleType("websockets")
websockets_sync = types.ModuleType("websockets.sync")
websockets_client = types.ModuleType("websockets.sync.client")

class DummyConnect:
    def __init__(self, *args, **kwargs):
        pass
    def __enter__(self):
        return MagicMock()
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

websockets_client.connect = DummyConnect
websockets_sync.client = websockets_client
websockets_mock.sync = websockets_sync
sys.modules["websockets"] = websockets_mock
sys.modules["websockets.sync"] = websockets_sync
sys.modules["websockets.sync.client"] = websockets_client

from skills.market_portfolio_realtime_websocket_feed import start_new, market_portfolio_realtime_websocket_feed


class TestMarketPortfolioRealtimeWebsocketFeed(unittest.TestCase):

    def test_start_new_initialization_and_handshake(self):
        rand_url = f"wss://{uuid.uuid4().hex}.io/stream"
        rand_token = uuid.uuid4().hex
        rand_symbol = uuid.uuid4().hex[:6].upper()
        rand_response = f"Data for {rand_symbol} received"

        mock_websocket_instance = MagicMock()
        mock_websocket_instance.recv.return_value = rand_response

        with patch("skills.market_portfolio_realtime_websocket_feed.connect", return_value=mock_websocket_instance) as mock_connect:
            result = start_new(url=rand_url, auth_token=rand_token, symbol=rand_symbol)
            mock_connect.assert_called_once_with(rand_url, timeout=5.0)
            mock_websocket_instance.send.assert_called_once_with(f'{{"auth": "{rand_token}"}}')
            self.assertEqual(result, {"symbol": rand_symbol})

    def test_start_new_stream_data_processing(self):
        rand_tracking_id = uuid.uuid4().hex

        with patch("requests.Session") as mock_session_cls:
            mock_session = mock_session_cls.return_value
            result = start_new(tracking_id=rand_tracking_id)
            mock_session.close.assert_called_once()
            self.assertEqual(result, {"tracking_id": rand_tracking_id})

    def test_start_new_exception_handling_on_failure(self):
        rand_url = f"wss://{uuid.uuid4().hex}.net/feed"
        random_error_message = uuid.uuid4().hex

        with patch("skills.market_portfolio_realtime_websocket_feed.connect", side_effect=Exception(random_error_message)) as mock_connect:
            with self.assertRaises(Exception) as ctx:
                start_new(url=rand_url)
            self.assertIn(random_error_message, str(ctx.exception))
            mock_connect.assert_called_once_with(rand_url, timeout=5.0)

    def test_start_new_payload_validation(self):
        rand_uuid = uuid.uuid4().hex
        rand_symbol = uuid.uuid4().hex[:5].upper()
        rand_price = round(random.uniform(10.0, 1000.0), 2)
        rand_volume = random.randint(100, 10000)

        payload = {
            "feed_uuid": rand_uuid,
            "symbol": rand_symbol,
            "price": rand_price,
            "volume": rand_volume
        }

        result = market_portfolio_realtime_websocket_feed(payload)

        self.assertEqual(result["status"], "connected")
        self.assertEqual(result["feed_uuid"], rand_uuid)
        self.assertEqual(result["symbol"], rand_symbol)
        self.assertEqual(result["price"], rand_price)
        self.assertEqual(result["volume"], rand_volume)

    def test_market_portfolio_realtime_websocket_feed_invalid_payload(self):
        invalid_payloads = [None, uuid.uuid4().hex, random.randint(1, 100), []]
        for payload in invalid_payloads:
            result = market_portfolio_realtime_websocket_feed(payload)
            self.assertEqual(result["status"], "connected")
            self.assertIsNone(result["feed_uuid"])
            self.assertIsNone(result["symbol"])
            self.assertIsNone(result["price"])
            self.assertIsNone(result["volume"])


if __name__ == "__main__":
    unittest.main()