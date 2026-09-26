import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys

from skills.market_insider_alert_pipeline import run_insider_alert_pipeline


class TestMarketInsiderAlertPipeline(unittest.TestCase):

    def setUp(self):
        self.random_ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/insider"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 9999999))
        self.random_storage = f"{uuid.uuid4().hex}.db"
        self.random_severity = random.choice(["HIGH", "CRITICAL", "MEDIUM"])
        self.random_threshold = round(random.uniform(10000.0, 1000000.0), 2)

        self.raw_data_stream = {
            "ticker": self.random_ticker,
            "shares": random.randint(1000, 50000),
            "value": self.random_threshold * 2,
            "is_anomaly": True
        }

    @patch('skills.market_insider_alert_pipeline.MarketInsiderActivityTracker')
    @patch('skills.market_insider_alert_pipeline.dispatch_portfolio_alerts')
    def test_pipeline_triggers_alert_on_anomaly(self, mock_dispatch, mock_tracker_class):
        mock_tracker_instance = mock_tracker_class.return_value
        mock_tracker_instance.analyze_activity.return_value = {
            "ticker": self.random_ticker,
            "status": "ANOMALY_DETECTED",
            "signature": uuid.uuid4().hex
        }

        config = {
            "url": self.random_url,
            "telegram_token": self.random_token,
            "chat_id": self.random_chat_id,
            "storage_file": self.random_storage,
            "severity_level": self.random_severity,
            "min_threshold": self.random_threshold,
            "channels": ["telegram"]
        }

        result = run_insider_alert_pipeline(self.raw_data_stream, config)

        mock_tracker_instance.analyze_activity.assert_called_once_with(self.raw_data_stream)
        mock_dispatch.assert_called_once_with(
            symbol=self.random_ticker,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage,
            severity_level=self.random_severity,
            min_threshold=self.random_threshold,
            channels=["telegram"]
        )
        self.assertTrue(result.get("alert_dispatched"))
        self.assertEqual(result.get("ticker"), self.random_ticker)

    @patch('skills.market_insider_alert_pipeline.MarketInsiderActivityTracker')
    @patch('skills.market_insider_alert_pipeline.dispatch_portfolio_alerts')
    def test_pipeline_skips_alert_on_normal_activity(self, mock_dispatch, mock_tracker_class):
        mock_tracker_instance = mock_tracker_class.return_value
        mock_tracker_instance.analyze_activity.return_value = {
            "ticker": self.random_ticker,
            "status": "NORMAL",
            "signature": uuid.uuid4().hex
        }

        config = {
            "url": self.random_url,
            "telegram_token": self.random_token,
            "chat_id": self.random_chat_id,
            "storage_file": self.random_storage,
            "severity_level": self.random_severity,
            "min_threshold": self.random_threshold,
            "channels": ["telegram"]
        }

        result = run_insider_alert_pipeline(self.raw_data_stream, config)

        mock_tracker_instance.analyze_activity.assert_called_once_with(self.raw_data_stream)
        mock_dispatch.assert_not_called()
        self.assertFalse(result.get("alert_dispatched"))
        self.assertEqual(result.get("ticker"), self.random_ticker)

    def test_pipeline_with_stream_bytes_io(self):
        garbage_bytes = uuid.uuid4().bytes + b"".join(bytes([random.randint(0, 255)]) for _ in range(32))
        stream_io = io.BytesIO(garbage_bytes)

        with patch('skills.market_insider_alert_pipeline.MarketInsiderActivityTracker') as mock_tracker_class, \
             patch('skills.market_insider_alert_pipeline.dispatch_portfolio_alerts') as mock_dispatch:

            mock_tracker_instance = mock_tracker_class.return_value
            mock_tracker_instance.analyze_activity.return_value = {
                "ticker": "BYTE_TICKER",
                "status": "CRITICAL",
                "signature": uuid.uuid4().hex
            }

            config = {
                "url": self.random_url,
                "telegram_token": self.random_token,
                "chat_id": self.random_chat_id,
                "storage_file": self.random_storage,
                "severity_level": self.random_severity,
                "min_threshold": self.random_threshold,
                "channels": ["api"]
            }

            stream_data = stream_io.read()
            result = run_insider_alert_pipeline(stream_data, config)

            self.assertIsNotNone(result)
            mock_dispatch.assert_called_once()


if __name__ == '__main__':
    unittest.main()