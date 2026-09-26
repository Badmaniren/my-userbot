import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import io

from skills import market_portfolio_alert_dispatcher


class TestMarketPortfolioAlertDispatcher(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:5]}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex}"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_send_telegram_notification(self):
        res = market_portfolio_alert_dispatcher.send_telegram_notification(
            self.telegram_token, self.chat_id, "Test Message"
        )
        self.assertTrue(res)

    @patch("skills.market_portfolio_alert_dispatcher.market_portfolio_monitor.run_pipeline")
    @patch("skills.market_portfolio_alert_dispatcher.market_portfolio_valuation.PortfolioValuation")
    def test_dispatch_portfolio_alerts_success(self, mock_valuation_cls, mock_run_pipeline):
        mock_valuation_inst = MagicMock()
        mock_valuation_inst.get_total_summary.return_value = "Summary text"
        mock_valuation_inst.calculate_portfolio_pnl.return_value = 150.0
        mock_valuation_cls.return_value = mock_valuation_inst

        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            self.symbol,
            self.url,
            self.telegram_token,
            self.chat_id,
            self.storage_file,
            severity_level="HIGH",
            min_threshold="MEDIUM"
        )

        self.assertEqual(result["status"], "dispatched")
        self.assertEqual(result["summary"], "Summary text")
        self.assertEqual(result["pnl"], 150.0)

    def test_dispatch_portfolio_alerts_filtered_out(self):
        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            self.symbol,
            self.url,
            self.telegram_token,
            self.chat_id,
            self.storage_file,
            severity_level="LOW",
            min_threshold="HIGH"
        )

        self.assertEqual(result["status"], "filtered_out")

    def test_process_stream_alert_returns_bytes_io(self):
        alert_id = uuid.uuid4().hex
        stream = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
        self.assertIsInstance(stream, io.BytesIO)

    def test_process_stream_alert_with_storage_file(self):
        alert_id = uuid.uuid4().hex
        stream = market_portfolio_alert_dispatcher.process_stream_alert(alert_id, storage_file=self.storage_file)
        self.assertIsInstance(stream, io.BytesIO)
