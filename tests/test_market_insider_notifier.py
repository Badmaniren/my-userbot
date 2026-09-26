import unittest
from unittest.mock import patch
import io
import random
import uuid
import string
from skills.market_insider_notifier import MarketInsiderNotifier, notify_market_insider


class TestMarketInsiderNotifier(unittest.TestCase):

    def setUp(self):
        self.token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 99999999))
        self.ticker = "".join(random.choices(string.ascii_uppercase, k=4))
        self.notifier = MarketInsiderNotifier(token=self.token, chat_id=self.chat_id, min_severity="MEDIUM")

    def test_handle_stream_event(self):
        rand_event_id = uuid.uuid4().hex
        mock_pipeline = unittest.mock.MagicMock()
        mock_pipeline.process_alert_stream.return_value = {"id": rand_event_id, "severity": "HIGH"}
        
        notifier = MarketInsiderNotifier(pipeline=mock_pipeline)
        stream_data = {"data": uuid.uuid4().hex}
        res = notifier.handle_stream_event(self.ticker, stream_data)

        mock_pipeline.process_alert_stream.assert_called_once_with(self.ticker, stream_data)
        self.assertEqual(res["id"], rand_event_id)
        self.assertEqual(res["severity"], "HIGH")

    def test_dispatch_notification_fallback(self):
        message = uuid.uuid4().hex
        mock_sender = unittest.mock.MagicMock(return_value=True)

        with patch("skills.market_insider_notifier.start_new", side_effect=TypeError("not supported")):
            notifier = MarketInsiderNotifier(token=self.token, chat_id=self.chat_id, telegram_sender=mock_sender)
            res = notifier.dispatch_notification(message)

        mock_sender.assert_called_once_with(self.token, self.chat_id, message)
        self.assertTrue(res)

    def test_io_byte_stream_handling(self):
        rand_bytes = uuid.uuid4().bytes + "".join(random.choices(string.ascii_letters, k=32)).encode('utf-8')
        byte_stream = io.BytesIO(rand_bytes)
        
        consumed = self.notifier.consume_stream_bytes(byte_stream)
        self.assertEqual(consumed, rand_bytes)

        plain_data = uuid.uuid4().hex
        self.assertEqual(self.notifier.consume_stream_bytes(plain_data), plain_data)

    def test_evaluate_exchange(self):
        exchange = uuid.uuid4().hex
        mock_pipeline = unittest.mock.MagicMock()
        mock_pipeline.evaluate_market_stream.return_value = {uuid.uuid4().hex: random.randint(1, 100)}

        notifier = MarketInsiderNotifier(pipeline=mock_pipeline)
        res = notifier.evaluate_exchange(exchange)

        mock_pipeline.evaluate_market_stream.assert_called_once_with(exchange)
        self.assertIsInstance(res, dict)

    def test_notify_market_insider_alias(self):
        msg = uuid.uuid4().hex
        with patch("skills.market_insider_notifier.send_telegram_notification", return_value=True) as mock_send:
            res = notify_market_insider(self.token, self.chat_id, msg)
            mock_send.assert_called_once_with(self.token, self.chat_id, msg)
            self.assertTrue(res)

    def test_process_and_notify_filtered_out(self):
        stream_data = {"severity": "LOW", "id": uuid.uuid4().hex}
        mock_pipeline = unittest.mock.MagicMock()
        mock_pipeline.process_alert_stream.return_value = stream_data

        notifier = MarketInsiderNotifier(
            token=self.token, 
            chat_id=self.chat_id, 
            min_severity="HIGH", 
            pipeline=mock_pipeline
        )
        
        with patch("skills.market_insider_notifier.start_new") as mock_start:
            res = notifier.process_and_notify(self.ticker, stream_data)
            self.assertFalse(res)
            mock_start.assert_not_called()

    def test_process_and_notify_success(self):
        event_id = uuid.uuid4().hex
        stream_data = {"severity": "CRITICAL", "id": event_id}
        mock_pipeline = unittest.mock.MagicMock()
        mock_pipeline.process_alert_stream.return_value = stream_data

        notifier = MarketInsiderNotifier(
            token=self.token, 
            chat_id=self.chat_id, 
            min_severity="MEDIUM", 
            pipeline=mock_pipeline
        )

        with patch("skills.market_insider_notifier.start_new", return_value=True) as mock_start:
            res = notifier.process_and_notify(self.ticker, stream_data)
            self.assertTrue(res)
            mock_start.assert_called_once()
            called_args = mock_start.call_args[0]
            self.assertEqual(called_args[0], self.token)
            self.assertEqual(called_args[1], self.chat_id)
            self.assertIn(event_id, called_args[2])

    def test_process_and_notify_with_bytes_stream(self):
        rand_bytes = uuid.uuid4().bytes + "".join(random.choices(string.ascii_letters, k=16)).encode('utf-8')
        byte_stream = io.BytesIO(rand_bytes)
        
        event_id = uuid.uuid4().hex
        mock_pipeline = unittest.mock.MagicMock()
        mock_pipeline.process_alert_stream.return_value = {"severity": "HIGH", "event_id": event_id}

        notifier = MarketInsiderNotifier(
            token=self.token,
            chat_id=self.chat_id,
            min_severity="LOW",
            pipeline=mock_pipeline
        )

        with patch("skills.market_insider_notifier.start_new", return_value=True) as mock_start:
            res = notifier.process_and_notify(self.ticker, byte_stream)
            self.assertTrue(res)
            mock_pipeline.process_alert_stream.assert_called_once_with(self.ticker, byte_stream)
            mock_start.assert_called_once()