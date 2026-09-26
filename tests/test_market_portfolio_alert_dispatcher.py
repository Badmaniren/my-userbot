import unittest
from unittest.mock import patch, MagicMock
import os
import io
import uuid
import random
import string

from skills.market_portfolio_alert_dispatcher import (
    send_telegram_notification,
    dispatch_portfolio_alerts,
    process_stream_alert
)

class TestMarketPortfolioAlertDispatcher(unittest.TestCase):

    def setUp(self):
        self.rand_str = lambda: ''.join(random.choices(string.ascii_letters, k=10))
        self.symbol = self.rand_str().upper()
        self.url = f"https://{self.rand_str()}.com/{self.rand_str()}"
        self.token = f"{random.randint(1000,9999)}:{self.rand_str()}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"/tmp/{uuid.uuid4().hex}_{self.rand_str()}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_send_telegram_notification(self):
        msg = f"Alert_{uuid.uuid4().hex}"
        res = send_telegram_notification(self.token, self.chat_id, msg)
        self.assertTrue(res)

    @patch('skills.market_portfolio_alert_dispatcher.market_portfolio_monitor')
    @patch('skills.market_portfolio_alert_dispatcher.market_portfolio_valuation')
    @patch('skills.market_portfolio_alert_dispatcher.send_telegram_notification')
    def test_dispatch_portfolio_alerts_filtered(self, mock_notify, mock_valuation, mock_monitor):
        severity = "LOW"
        min_thresh = "HIGH"
        
        result = dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=severity,
            min_threshold=min_thresh
        )
        
        self.assertEqual(result.get("status"), "filtered_out")
        mock_monitor.run_pipeline.assert_not_called()
        mock_notify.assert_not_called()

    @patch('skills.market_portfolio_alert_dispatcher.market_portfolio_monitor')
    @patch('skills.market_portfolio_alert_dispatcher.market_portfolio_valuation')
    @patch('skills.market_portfolio_alert_dispatcher.send_telegram_notification')
    def test_dispatch_portfolio_alerts_dispatched(self, mock_notify, mock_valuation_cls, mock_monitor):
        severity = "CRITICAL"
        min_thresh = "MEDIUM"
        
        expected_summary = f"Summary_{uuid.uuid4().hex}"
        expected_pnl = round(random.uniform(-1000.0, 1000.0), 2)
        
        mock_val_instance = MagicMock()
        mock_val_instance.get_total_summary.return_value = expected_summary
        mock_val_instance.calculate_portfolio_pnl.return_value = expected_pnl
        mock_valuation_cls.PortfolioValuation.return_value = mock_val_instance

        result = dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=severity,
            min_threshold=min_thresh,
            channels=["telegram"]
        )
        
        self.assertEqual(result.get("status"), "dispatched")
        self.assertEqual(result.get("summary"), expected_summary)
        self.assertEqual(result.get("pnl"), expected_pnl)
        
        mock_monitor.run_pipeline.assert_called_once_with(
            self.symbol, self.url, self.token, self.chat_id, self.storage_file
        )
        mock_notify.assert_called_once()
        self.assertTrue(os.path.exists(self.storage_file))

    @patch('skills.market_portfolio_alert_dispatcher.market_report_generator')
    def test_process_stream_alert_success(self, mock_report_gen_module):
        alert_id = uuid.uuid4().hex
        expected_bytes = io.BytesIO(uuid.uuid4().bytes)
        
        mock_gen_instance = MagicMock()
        mock_gen_instance.get_raw_stream_dump.return_value = expected_bytes
        mock_report_gen_module.MarketReportGenerator.return_value = mock_gen_instance

        res = process_stream_alert(alert_id)
        self.assertEqual(res, expected_bytes)
        mock_gen_instance.get_raw_stream_dump.assert_called_once_with(alert_id)

    @patch('skills.market_portfolio_alert_dispatcher.market_report_generator')
    def test_process_stream_alert_fallback_no_args(self, mock_report_gen_module):
        alert_id = uuid.uuid4().hex
        expected_bytes = io.BytesIO(uuid.uuid4().bytes)
        
        mock_gen_instance = MagicMock()
        mock_gen_instance.get_raw_stream_dump.side_effect = [TypeError, expected_bytes]
        mock_report_gen_module.MarketReportGenerator.return_value = mock_gen_instance

        res = process_stream_alert(alert_id)
        self.assertEqual(res, expected_bytes)
        self.assertEqual(mock_gen_instance.get_raw_stream_dump.call_count, 2)

    @patch('skills.market_portfolio_alert_dispatcher.market_report_generator')
    def test_process_stream_alert_fallback_empty(self, mock_report_gen_module):
        alert_id = uuid.uuid4().hex
        
        mock_gen_instance = MagicMock()
        mock_gen_instance.get_raw_stream_dump.side_effect = TypeError
        mock_report_gen_module.MarketReportGenerator.return_value = mock_gen_instance

        res = process_stream_alert(alert_id)
        self.assertIsInstance(res, io.BytesIO)
        self.assertEqual(res.read(), b"")

    @patch('skills.market_portfolio_alert_dispatcher.market_report_generator', None)
    def test_process_stream_alert_none_generator(self):
        alert_id = uuid.uuid4().hex
        res = process_stream_alert(alert_id)
        self.assertIsInstance(res, io.BytesIO)
        self.assertEqual(res.read(), b"")

if __name__ == '__main__':
    unittest.main()