import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json
import asyncio

from skills.market_portfolio_realtime_ws_listener import (
    MarketPortfolioRealtimeWsListener,
    WebSocketConnectionError,
    InvalidMessageError
)

class TestMarketPortfolioRealtimeWsListener(unittest.TestCase):

    def setUp(self):
        self.random_uri = f"wss://exchange.{uuid.uuid4().hex[:8]}.io/ws/{random.randint(1000, 9999)}"
        self.random_channel = "".join(random.choices(string.ascii_lowercase, k=10))
        self.listener = MarketPortfolioRealtimeWsListener(uri=self.random_uri, channel=self.random_channel)

    def test_initialization_state(self):
        self.assertEqual(self.listener.uri, self.random_uri)
        self.assertEqual(self.listener.channel, self.random_channel)
        self.assertFalse(self.listener.is_connected)

    def test_validate_message_success(self):
        valid_id = str(uuid.uuid4())
        random_price = round(random.uniform(10.0, 5000.0), 4)
        random_symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        
        raw_payload = json.dumps({
            "event_id": valid_id,
            "symbol": random_symbol,
            "price": random_price,
            "status": "active"
        })

        parsed = self.listener.validate_and_parse(raw_payload)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["event_id"], valid_id)
        self.assertEqual(parsed["symbol"], random_symbol)
        self.assertEqual(parsed["price"], random_price)

    def test_validate_message_invalid_json(self):
        garbage_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        raw_payload = f"INVALID_JSON_{garbage_bytes}"

        with self.assertRaises(InvalidMessageError):
            self.listener.validate_and_parse(raw_payload)

    def test_validate_message_missing_required_fields(self):
        missing_id_payload = json.dumps({
            "symbol": "".join(random.choices(string.ascii_uppercase, k=3)),
            "price": random.randint(1, 100)
        })

        with self.assertRaises(InvalidMessageError):
            self.listener.validate_and_parse(missing_id_payload)

    def test_stream_ingestion_loop(self):
        event_id = uuid.uuid4().hex
        symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        price = round(random.uniform(1.0, 1000.0), 2)
        
        mock_messages = [
            json.dumps({"event_id": event_id, "symbol": symbol, "price": price}),
            None
        ]

        with patch('skills.market_portfolio_realtime_ws_listener.websockets.connect') as mock_connect:
            mock_ws = MagicMock()
            mock_ws.recv.side_effect = mock_messages
            mock_connect.return_value.__aenter__.return_value = mock_ws

            received_data = []
            def callback(msg):
                received_data.append(msg)

            self.listener.on_message_callback = callback

            try:
                asyncio.run(self.listener.connect_and_listen())
            except Exception:
                pass

            self.assertTrue(len(received_data) > 0)
            self.assertEqual(received_data[0]["event_id"], event_id)
            self.assertEqual(received_data[0]["symbol"], symbol)
            self.assertEqual(received_data[0]["price"], price)

    def test_reconnection_logic_on_failure(self):
        fail_attempts = random.randint(2, 4)
        success_id = uuid.uuid4().hex

        side_effects = [Exception("Network down")] * fail_attempts
        
        mock_ws = MagicMock()
        mock_ws.recv.return_value = json.dumps({"event_id": success_id, "symbol": "BTC", "price": 123.45})

        with patch('skills.market_portfolio_realtime_ws_listener.websockets.connect') as mock_connect:
            mock_connect.side_effect = side_effects + [MagicMock(__aenter__=MagicMock(return_value=mock_ws))]
            
            with patch('asyncio.sleep', return_value=None) as mock_sleep:
                try:
                    asyncio.run(self.listener.connect_and_listen(max_retries=fail_attempts + 1))
                except Exception:
                    pass

                self.assertGreaterEqual(mock_connect.call_count, fail_attempts)
                self.assertEqual(mock_sleep.call_count, fail_attempts)

    def test_stream_io_buffer_processing(self):
        stream_token = uuid.uuid4().hex
        stream_data = f"{{\n  \"event_id\": \"{stream_token}\",\n  \"symbol\": \"ETH\",\n  \"price\": 999.99\n}}\n".encode('utf-8')
        
        mock_io = io.BytesIO(stream_data)
        
        result = self.listener.process_stream_buffer(mock_io)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["event_id"], stream_token)
        self.assertEqual(result["symbol"], "ETH")
        self.assertEqual(result["price"], 999.99)