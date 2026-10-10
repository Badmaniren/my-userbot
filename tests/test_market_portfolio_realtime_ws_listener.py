import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
import io
import json
import uuid
import random
import string
from skills.market_portfolio_realtime_ws_listener import (
    MarketPortfolioRealtimeWsListener,
    market_portfolio_realtime_ws_listener,
    WebSocketConnectionError,
    InvalidMessageError,
    websockets
)


class TestMarketPortfolioRealtimeWsListener(unittest.TestCase):

    def setUp(self):
        self.random_uri = f"ws://{uuid.uuid4().hex}.local/{uuid.uuid4().hex}"
        self.random_channel = uuid.uuid4().hex
        self.random_file = f"{uuid.uuid4().hex}.log"
        self.random_event_id = uuid.uuid4().hex
        self.listener = MarketPortfolioRealtimeWsListener(
            uri=self.random_uri,
            channel=self.random_channel,
            target_file=self.random_file,
            expected_event_id=self.random_event_id
        )

    def test_factory_function(self):
        inst = market_portfolio_realtime_ws_listener(
            uri=self.random_uri,
            channel=self.random_channel,
            target_file=self.random_file,
            expected_event_id=self.random_event_id
        )
        self.assertIsInstance(inst, MarketPortfolioRealtimeWsListener)
        self.assertEqual(inst.uri, self.random_uri)
        self.assertEqual(inst.channel, self.random_channel)
        self.assertEqual(inst.target_file, self.random_file)
        self.assertEqual(inst.expected_event_id, self.random_event_id)

    def test_validate_and_parse_success(self):
        sym = ''.join(random.choices(string.ascii_uppercase, k=5))
        prc = round(random.uniform(10.0, 1000.0), 2)
        payload = json.dumps({
            "event_id": self.random_event_id,
            "symbol": sym,
            "price": prc,
            "extra": uuid.uuid4().hex
        })
        parsed = self.listener.validate_and_parse(payload)
        self.assertEqual(parsed["event_id"], self.random_event_id)
        self.assertEqual(parsed["symbol"], sym)
        self.assertEqual(parsed["price"], prc)

    def test_validate_and_parse_invalid_json(self):
        bad_json = uuid.uuid4().hex + "{"
        with self.assertRaises(InvalidMessageError):
            self.listener.validate_and_parse(bad_json)

    def test_validate_and_parse_not_dict(self):
        not_a_dict = json.dumps([random.randint(1, 100), uuid.uuid4().hex])
        with self.assertRaises(InvalidMessageError):
            self.listener.validate_and_parse(not_a_dict)

    def test_validate_and_parse_missing_fields(self):
        partial_data = json.dumps({
            "event_id": self.random_event_id,
            "symbol": uuid.uuid4().hex
        })
        with self.assertRaises(InvalidMessageError):
            self.listener.validate_and_parse(partial_data)

    def test_process_stream_buffer(self):
        sym = uuid.uuid4().hex
        prc = random.random() * 500
        raw_dict = {
            "event_id": self.random_event_id,
            "symbol": sym,
            "price": prc
        }
        stream_data = io.BytesIO(json.dumps(raw_dict).encode('utf-8'))
        res = self.listener.process_stream_buffer(stream_data)
        self.assertEqual(res["symbol"], sym)
        self.assertEqual(res["price"], prc)

    def test_process_raw_message_with_target_file(self):
        sym = uuid.uuid4().hex
        prc = random.random() * 100
        raw_dict = {
            "event_id": self.random_event_id,
            "symbol": sym,
            "price": prc
        }
        msg = json.dumps(raw_dict)
        mock_file_open = MagicMock()
        
        async def run_test():
            with patch("builtins.open", mock_file_open):
                res = await self.listener.process_raw_message(msg)
                self.assertEqual(res["event_id"], self.random_event_id)
                mock_file_open.assert_called_once_with(self.random_file, "a")

        asyncio.run(run_test())

    def test_connect_and_listen_missing_websockets(self):
        with patch("skills.market_portfolio_realtime_ws_listener.websockets", None):
            with self.assertRaises(WebSocketConnectionError):
                asyncio.run(self.listener.connect_and_listen(max_retries=1))

    def test_stream_ingestion_loop(self):
        if websockets is None:
            self.skipTest("websockets module not present")

        sym = uuid.uuid4().hex
        prc = random.random() * 1000
        msg_str = json.dumps({
            "event_id": self.random_event_id,
            "symbol": sym,
            "price": prc
        })

        mock_ws = AsyncMock()
        mock_ws.recv.side_effect = [msg_str, None]

        mock_connect_context = AsyncMock()
        mock_connect_context.__aenter__.return_value = mock_ws

        callback_mock = MagicMock()
        self.listener.on_message_callback = callback_mock

        with patch('skills.market_portfolio_realtime_ws_listener.websockets.connect', return_value=mock_connect_context) as mock_connect:
            asyncio.run(self.listener.connect_and_listen(max_retries=1))
            mock_connect.assert_called_once_with(self.random_uri)
            callback_mock.assert_called_once()
            args, _ = callback_mock.call_args
            self.assertEqual(args[0]["symbol"], sym)

    def test_reconnection_logic_on_failure(self):
        if websockets is None:
            self.skipTest("websockets module not present")

        with patch('skills.market_portfolio_realtime_ws_listener.websockets.connect', side_effect=Exception(uuid.uuid4().hex)) as mock_connect:
            with self.assertRaises(WebSocketConnectionError):
                asyncio.run(self.listener.connect_and_listen(max_retries=2))
            self.assertGreaterEqual(mock_connect.call_count, 2)
            self.assertFalse(self.listener.is_connected)