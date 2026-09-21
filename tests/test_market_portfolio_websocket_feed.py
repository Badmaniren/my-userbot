import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json
import os

from skills.market_portfolio_websocket_feed import WebSocketFeedProcessor

class TestWebSocketFeedProcessor(unittest.TestCase):

    def setUp(self):
        self.rand_storage = f"{uuid.uuid4().hex}.json"
        self.rand_ws_url = f"wss://market-{uuid.uuid4().hex[:8]}.io/stream"
        self.processor = WebSocketFeedProcessor(storage_file=self.rand_storage, ws_url=self.rand_ws_url)

    def tearDown(self):
        if os.path.exists(self.rand_storage):
            try:
                os.remove(self.rand_storage)
            except OSError:
                pass

    def test_init_sets_attributes(self):
        rand_file = f"{uuid.uuid4().hex}.db"
        rand_url = f"wss://stream.{uuid.uuid4().hex}.net/v1"
        proc = WebSocketFeedProcessor(storage_file=rand_file, ws_url=rand_url)
        self.assertEqual(proc.storage_file, rand_file)
        self.assertEqual(proc.ws_url, rand_url)
        self.assertIsInstance(proc._active_connections, int)

    def test_parse_incoming_payload_valid(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_price = round(random.uniform(10.0, 5000.0), 4)
        rand_timestamp = random.randint(1600000000, 1800000000)

        payload = json.dumps({
            "symbol": rand_symbol,
            "price": rand_price,
            "timestamp": rand_timestamp
        })

        result = self.processor.parse_incoming_payload(payload)
        self.assertIsNotNone(result)
        self.assertEqual(result["symbol"], rand_symbol)
        self.assertEqual(result["price"], rand_price)
        self.assertEqual(result["timestamp"], rand_timestamp)

    def test_parse_incoming_payload_invalid(self):
        rand_garbage = ''.join(random.choices(string.ascii_letters + string.punctuation, k=30))
        result = self.processor.parse_incoming_payload(rand_garbage)
        self.assertIsNone(result)

    def test_prepare_alert_trigger_data(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        rand_price = round(random.uniform(100.0, 9999.0), 2)
        rand_threshold = round(rand_price * random.uniform(0.9, 1.1), 2)

        data = {
            "symbol": rand_symbol,
            "price": rand_price,
            "timestamp": random.randint(100000, 999999)
        }

        alert_packet = self.processor.prepare_alert_trigger_data(data, threshold=rand_threshold)
        self.assertIsInstance(alert_packet, dict)
        self.assertEqual(alert_packet["symbol"], rand_symbol)
        self.assertEqual(alert_packet["current_price"], rand_price)
        self.assertEqual(alert_packet["threshold"], rand_threshold)
        self.assertIn("triggered", alert_packet)
        if rand_price >= rand_threshold:
            self.assertTrue(alert_packet["triggered"])
        else:
            self.assertFalse(alert_packet["triggered"])

    def test_store_feed_datapoint(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=3))
        rand_price = round(random.uniform(1.0, 500.0), 2)

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            self.processor.store_feed_datapoint(rand_symbol, rand_price)
            mock_file.assert_called_once_with(self.rand_storage, "a", encoding="utf-8")
            handle = mock_file()
            handle.write.assert_called()

    def test_connect_and_consume_stream(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        rand_price = round(random.uniform(50.0, 1000.0), 2)

        mock_ws_client = MagicMock()
        mock_ws_instance = MagicMock()
        mock_ws_instance.recv.return_value = json.dumps({
            "symbol": rand_symbol,
            "price": rand_price,
            "timestamp": 1234567890
        })
        mock_ws_client.connect.return_value = mock_ws_instance

        with patch("skills.market_portfolio_websocket_feed.ws_client", mock_ws_client):
            with patch.object(self.processor, "store_feed_datapoint") as mock_store:

                mock_ws_instance.__enter__.return_value = mock_ws_instance

                success = self.processor.consume_single_tick()

                mock_ws_client.connect.assert_called_once_with(self.rand_ws_url)
                self.assertTrue(success)
                mock_store.assert_called_once_with(rand_symbol, rand_price)

    def test_get_live_feed_summary(self):
        rand_count = random.randint(5, 50)
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=3))

        mock_lines = []
        for _ in range(rand_count):
            mock_lines.append(json.dumps({
                "symbol": rand_symbol,
                "price": round(random.uniform(10.0, 100.0), 2),
                "timestamp": random.randint(1000, 9999)
            }) + "\n")

        fake_file_data = "".join(mock_lines)

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", unittest.mock.mock_open(read_data=fake_file_data)):
                summary = self.processor.get_live_feed_summary(rand_symbol)
                self.assertEqual(summary["total_ticks"], rand_count)
                self.assertEqual(summary["symbol"], rand_symbol)
                self.assertIn("avg_price", summary)
                self.assertIn("max_price", summary)
                self.assertIn("min_price", summary)