import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_insider_alert_pipeline import (
    run_insider_alert_pipeline,
    MarketInsiderAlertPipelineModuleAPI
)


class TestMarketInsiderAlertPipeline(unittest.TestCase):

    def setUp(self):
        self.random_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.random_stream = f"STREAM_{uuid.uuid4().hex}"
        self.random_url = f"https://example.com/api/{uuid.uuid4().hex[:8]}"
        self.random_token = f"BOT:{uuid.uuid4().hex[:10]}"
        self.random_chat_id = f"CHAT_{random.randint(100000, 999999)}"
        self.random_storage = f"storage_{uuid.uuid4().hex[:8]}.db"
        self.random_db_path = f"db_{uuid.uuid4().hex[:8]}.sqlite"
        self.random_signature = f"sig_{uuid.uuid4().hex[:10]}"
        self.severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    @patch("skills.market_insider_alert_pipeline.MarketInsiderActivityTracker")
    @patch("skills.market_insider_alert_pipeline.dispatch_portfolio_alerts")
    def test_run_pipeline_anomaly_detected(self, mock_dispatch, mock_tracker_cls):
        mock_tracker_instance = MagicMock()
        mock_tracker_instance.analyze_activity.return_value = {
            "status": "anomaly",
            "signature": self.random_signature,
            "ticker": self.random_ticker
        }
        mock_tracker_cls.return_value = mock_tracker_instance

        channels_list = ["telegram", "webhook"]
        min_thresh = random.uniform(50.0, 500.0)
        sev_level = random.choice(self.severity_levels)

        result = run_insider_alert_pipeline(
            raw_data_stream=self.random_stream,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage,
            severity_level=sev_level,
            min_threshold=min_thresh,
            channels=channels_list,
            ticker=self.random_ticker,
            db_path=self.random_db_path,
            signature=self.random_signature
        )

        self.assertEqual(result["status"], "anomaly")
        self.assertEqual(result["signature"], self.random_signature)
        self.assertEqual(result["ticker"], self.random_ticker)
        self.assertTrue(result["alert_sent"])

        mock_tracker_cls.assert_called_once_with(db_path=self.random_db_path)
        mock_tracker_instance.analyze_activity.assert_called_once()
        mock_dispatch.assert_called_once_with(
            symbol=self.random_ticker,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage,
            severity_level=sev_level,
            min_threshold=min_thresh,
            channels=channels_list
        )

    @patch("skills.market_insider_alert_pipeline.MarketInsiderActivityTracker")
    @patch("skills.market_insider_alert_pipeline.dispatch_portfolio_alerts")
    def test_run_pipeline_normal_activity(self, mock_dispatch, mock_tracker_cls):
        mock_tracker_instance = MagicMock()
        mock_tracker_instance.analyze_activity.return_value = {
            "status": "normal",
            "signature": self.random_signature,
            "ticker": self.random_ticker
        }
        mock_tracker_cls.return_value = mock_tracker_instance

        result = run_insider_alert_pipeline(
            raw_data_stream={"ticker": self.random_ticker, "data": self.random_stream},
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage,
            severity_level="LOW",
            min_threshold=10.0,
            channels=["telegram"]
        )

        self.assertEqual(result["status"], "normal")
        self.assertEqual(result["ticker"], self.random_ticker)
        self.assertFalse(result["alert_sent"])
        mock_dispatch.assert_not_called()

    @patch("skills.market_insider_alert_pipeline.MarketInsiderActivityTracker")
    @patch("skills.market_insider_alert_pipeline.dispatch_portfolio_alerts")
    def test_module_api_execute_pipeline(self, mock_dispatch, mock_tracker_cls):
        mock_tracker_instance = MagicMock()
        mock_tracker_instance.analyze_activity.return_value = {
            "status": "anomaly",
            "signature": self.random_signature,
            "ticker": self.random_ticker
        }
        mock_tracker_cls.return_value = mock_tracker_instance

        payload = {
            "ticker": self.random_ticker,
            "raw_data_stream": self.random_stream,
            "url": self.random_url,
            "telegram_token": self.random_token,
            "chat_id": self.random_chat_id,
            "storage_file": self.random_storage,
            "severity_level": "HIGH",
            "min_threshold": 250.0,
            "channels": ["telegram"],
            "db_path": self.random_db_path,
            "signature": self.random_signature
        }

        api = MarketInsiderAlertPipelineModuleAPI()
        result = api.execute_pipeline(payload)

        self.assertEqual(result["status"], "anomaly")
        self.assertTrue(result["alert_sent"])
        self.assertEqual(result["ticker"], self.random_ticker)
        self.assertEqual(result["signature"], self.random_signature)
        mock_dispatch.assert_called_once()