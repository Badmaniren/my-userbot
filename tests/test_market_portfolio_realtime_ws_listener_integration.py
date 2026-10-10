import unittest
import asyncio
import json
import os
import uuid
import random
from skills.market_portfolio_realtime_ws_listener import (
    market_portfolio_realtime_ws_listener,
    InvalidMessageError,
    WebSocketConnectionError
)


class TestMarketPortfolioRealtimeWsListenerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_event_id = str(uuid.uuid4())
        self.test_symbol = f"SYM_{random.randint(1000, 9999)}"
        self.test_price = round(random.uniform(10.0, 1500.0), 2)
        self.target_file = f"test_stream_{uuid.uuid4()}.log"

    def tearDown(self):
        if os.path.exists(self.target_file):
            try:
                os.remove(self.target_file)
            except OSError:
                pass

    def test_validate_and_parse_success(self):
        listener = market_portfolio_realtime_ws_listener()
        payload = json.dumps({
            "event_id": self.test_event_id,
            "symbol": self.test_symbol,
            "price": self.test_price
        })

        parsed = listener.validate_and_parse(payload)
        self.assertEqual(parsed["event_id"], self.test_event_id)
        self.assertEqual(parsed["symbol"], self.test_symbol)
        self.assertEqual(parsed["price"], self.test_price)

    def test_validate_and_parse_invalid_json(self):
        listener = market_portfolio_realtime_ws_listener()
        invalid_payload = "{invalid_json"

        with self.assertRaises(InvalidMessageError):
            listener.validate_and_parse(invalid_payload)

    def test_validate_and_parse_missing_fields(self):
        listener = market_portfolio_realtime_ws_listener()
        payload = json.dumps({
            "event_id": self.test_event_id,
            "symbol": self.test_symbol
            # missing price
        })

        with self.assertRaises(InvalidMessageError):
            listener.validate_and_parse(payload)

    def test_process_raw_message_with_file_output(self):
        listener = market_portfolio_realtime_ws_listener(target_file=self.target_file)
        payload_dict = {
            "event_id": self.test_event_id,
            "symbol": self.test_symbol,
            "price": self.test_price
        }
        raw_message = json.dumps(payload_dict)

        parsed = asyncio.run(listener.process_raw_message(raw_message))

        self.assertEqual(parsed["event_id"], self.test_event_id)
        self.assertTrue(os.path.exists(self.target_file))

        with open(self.target_file, "r") as f:
            content = f.read().strip()

        self.assertEqual(content, raw_message)

    def test_connect_and_listen_failure_handling(self):
        fake_uri = f"ws://localhost:{random.randint(10000, 65535)}/{uuid.uuid4()}"
        listener = market_portfolio_realtime_ws_listener(uri=fake_uri)

        with self.assertRaises(WebSocketConnectionError):
            asyncio.run(listener.connect_and_listen(max_retries=1))


if __name__ == "__main__":
    unittest.main()