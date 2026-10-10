import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json

from skills.market_portfolio_realtime_websocket_hub import (
    MarketPortfolioRealtimeWebsocketHub,
    WebsocketHubException
)

class TestMarketPortfolioRealtimeWebsocketHub(unittest.TestCase):

    def setUp(self):
        self.endpoint_url = f"wss://{uuid.uuid4().hex}.market-stream.net/{uuid.uuid4().hex}"
        self.client_id = f"client_{uuid.uuid4().hex[:8]}"
        self.hub = MarketPortfolioRealtimeWebsocketHub(endpoint=self.endpoint_url)

    def test_initialization_state(self):
        self.assertEqual(self.hub.endpoint, self.endpoint_url)
        self.assertFalse(self.hub.is_connected)
        self.assertEqual(len(self.hub.active_subscriptions), 0)

    def test_successful_connection_and_handshake(self):
        mock_ws = MagicMock()
        mock_ws.recv.return_value = json.dumps({
            "status": "authorized",
            "session_id": uuid.uuid4().hex
        })

        with patch("skills.market_portfolio_realtime_websocket_hub.websockets.connect", return_value=mock_ws) as mock_connect:
            connection_result = self.hub.connect(client_id=self.client_id)
            
            mock_connect.assert_called_once_with(self.endpoint_url)
            self.assertTrue(connection_result)
            self.assertTrue(self.hub.is_connected)

    def test_connection_failure_raises_exception(self):
        with patch("skills.market_portfolio_realtime_websocket_hub.websockets.connect", side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(WebsocketHubException):
                self.hub.connect(client_id=self.client_id)
            self.assertFalse(self.hub.is_connected)

    def test_subscribe_to_ticker_streams(self):
        ticker_symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        mock_ws = MagicMock()
        self.hub._ws_connection = mock_ws
        self.hub.is_connected = True

        response_payload = json.dumps({
            "event": "subscribed",
            "channel": ticker_symbol,
            "nonce": uuid.uuid4().hex
        })
        mock_ws.recv.return_value = response_payload

        result = self.hub.subscribe(ticker_symbol)

        self.assertTrue(result)
        self.assertIn(ticker_symbol, self.hub.active_subscriptions)
        mock_ws.send.assert_called_once()
        sent_data = json.loads(mock_ws.send.call_args[0][0])
        self.assertEqual(sent_data["action"], "subscribe")
        self.assertEqual(sent_data["symbol"], ticker_symbol)

    def test_unsubscribe_from_ticker_streams(self):
        ticker_symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.hub.active_subscriptions.add(ticker_symbol)
        
        mock_ws = MagicMock()
        self.hub._ws_connection = mock_ws
        self.hub.is_connected = True

        mock_ws.recv.return_value = json.dumps({
            "event": "unsubscribed",
            "channel": ticker_symbol
        })

        result = self.hub.unsubscribe(ticker_symbol)

        self.assertTrue(result)
        self.assertNotIn(ticker_symbol, self.hub.active_subscriptions)

    def test_incoming_stream_parsing_and_dispatch(self):
        random_price = round(random.uniform(10.0, 1500.0), 4)
        random_volume = random.randint(100, 50000)
        ticker_symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"

        raw_stream_frame = json.dumps({
            "type": "quote",
            "symbol": ticker_symbol,
            "price": random_price,
            "volume": random_volume,
            "timestamp": uuid.uuid4().hex
        })

        mock_callback = MagicMock()
        self.hub.register_stream_callback(ticker_symbol, mock_callback)

        self.hub._handle_incoming_message(raw_stream_frame)

        mock_callback.assert_called_once()
        called_arg = mock_callback.call_args[0][0]
        self.assertEqual(called_arg["symbol"], ticker_symbol)
        self.assertEqual(called_arg["price"], random_price)
        self.assertEqual(called_arg["volume"], random_volume)

    def test_malformed_incoming_payload_handling(self):
        garbage_stream = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
        stream_io = io.BytesIO(garbage_stream.encode('utf-8'))

        with patch("skills.market_portfolio_realtime_websocket_hub.logging") as mock_logging:
            self.hub._process_stream_buffer(stream_io)
            mock_logging.error.assert_called()

    def test_heartbeat_ping_pong_mechanism(self):
        mock_ws = MagicMock()
        self.hub._ws_connection = mock_ws
        self.hub.is_connected = True

        ping_payload = json.dumps({"ping": uuid.uuid4().hex})
        mock_ws.recv.return_value = ping_payload

        self.hub._evaluate_heartbeat()

        mock_ws.send.assert_called_once()
        sent_msg = json.loads(mock_ws.send.call_args[0][0])
        self.assertIn("pong", sent_msg)

    def test_graceful_disconnect(self):
        mock_ws = MagicMock()
        self.hub._ws_connection = mock_ws
        self.hub.is_connected = True

        self.hub.disconnect()

        mock_ws.close.assert_called_once()
        self.assertFalse(self.hub.is_connected)
        self.assertIsNone(self.hub._ws_connection)