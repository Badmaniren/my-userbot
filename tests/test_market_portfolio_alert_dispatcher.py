import os
import io
import uuid
import random
import unittest
from unittest.mock import patch, MagicMock

from skills.market_portfolio_alert_dispatcher import (
    send_telegram_notification,
    dispatch_portfolio_alerts,
    process_stream_alert
)

class TestMarketPortfolioAlertDispatcher(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex[:8]}"
        self.telegram_token = f"{random.randint(100000, 999999)}:ABC{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        self.alert_id = uuid.uuid4().hex

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_send_telegram_notification_success(self):
        message = f"Test message {uuid.uuid4().hex}"
        result = send_telegram_notification(self.telegram_token, self.chat_id, message)
        self.assertTrue(result)

    @patch('skills.market_portfolio_alert_dispatcher.market_report_generator')
    def test_process_stream_alert_with_generator(self, mock_generator_mod):
        expected_bytes = io.BytesIO(f"stream_data_{uuid.uuid4().hex}".encode('utf-8'))
        mock_instance = MagicMock()
        mock_instance.get_raw_stream_dump.return_value = expected_bytes
        mock_generator_mod.MarketReportGenerator.return_value = mock_instance

        result = process_stream_alert(self.alert_id)
        mock_instance.get_raw_stream_dump.assert_called_once()
        self.assertEqual(result, expected_bytes)

    @patch('skills.market_portfolio_alert_dispatcher.market_report_generator', None)
    def test_process_stream_alert_no_generator(self):
        result = process_stream_alert(self.alert_id)
        self.assertIsInstance(result, io.BytesIO)
        self.assertEqual(result.read(), b"")

    @patch('skills.market_portfolio_alert_dispatcher.send_telegram_notification')
    @patch('skills.market_portfolio_alert_dispatcher.market_portfolio_valuation')
    @patch('skills.market_portfolio_alert_dispatcher.market_portfolio_monitor')
    def test_dispatch_portfolio_alerts_flow(self, mock_monitor, mock_valuation_mod, mock_send_telegram):
        expected_summary = f"Summary_{uuid.uuid4().hex[:6]}"
        expected_pnl = float(random.randint(-10000, 10000)) + random.random()

        mock_valuation_instance = MagicMock()
        mock_valuation_instance.get_total_summary.return_value = expected_summary
        mock_valuation_instance.calculate_portfolio_pnl.return_value = expected_pnl
        mock_valuation_mod.PortfolioValuation.return_value = mock_valuation_instance

        mock_send_telegram.return_value = True

        result = dispatch_portfolio_alerts(
            self.symbol,
            self.url,
            self.telegram_token,
            self.chat_id,
            self.storage_file
        )

        mock_monitor.run_pipeline.assert_called_once_with(
            self.symbol,
            self.url,
            self.telegram_token,
            self.chat_id,
            self.storage_file
        )
        mock_valuation_mod.PortfolioValuation.assert_called_once_with(storage_file=self.storage_file)
        mock_valuation_instance.get_total_summary.assert_called_once_with(self.url)
        mock_valuation_instance.calculate_portfolio_pnl.assert_called_once_with(self.url)

        expected_message = f"Portfolio Alert:\n{expected_summary}\nPNL: {expected_pnl}"
        mock_send_telegram.assert_called_once_with(
            self.telegram_token,
            self.chat_id,
            expected_message
        )

        self.assertEqual(result, {
            "summary": expected_summary,
            "pnl": expected_pnl,
            "status": "dispatched"
        })
        self.assertTrue(os.path.exists(self.storage_file))

    @patch('skills.market_portfolio_alert_dispatcher.send_telegram_notification')
    @patch('skills.market_portfolio_alert_dispatcher.market_portfolio_valuation')
    @patch('skills.market_portfolio_alert_dispatcher.market_portfolio_monitor')
    def test_dispatch_portfolio_alerts_creates_missing_storage(self, mock_monitor, mock_valuation_mod, mock_send_telegram):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

        mock_valuation_instance = MagicMock()
        mock_valuation_instance.get_total_summary.return_value = "summary"
        mock_valuation_instance.calculate_portfolio_pnl.return_value = 0.0
        mock_valuation_mod.PortfolioValuation.return_value = mock_valuation_instance

        dispatch_portfolio_alerts(
            self.symbol,
            self.url,
            self.telegram_token,
            self.chat_id,
            self.storage_file
        )

        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, 'r') as f:
            content = f.read()
            self.assertEqual(content, '{}')

    @patch('skills.market_portfolio_alert_dispatcher.send_telegram_notification')
    def test_dispatch_portfolio_alerts_keyword_args_custom_message(self, mock_send_telegram):
        custom_msg = f"Custom alert {uuid.uuid4().hex}"
        result = dispatch_portfolio_alerts(
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            message=custom_msg
        )
        mock_send_telegram.assert_called_once_with(
            self.telegram_token,
            self.chat_id,
            custom_msg
        )
        self.assertEqual(result["status"], "dispatched")

if __name__ == '__main__':
    unittest.main()