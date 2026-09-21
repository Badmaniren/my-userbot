import os
import io
import random
import uuid
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
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:20]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_send_telegram_notification_success(self):
        token = self.telegram_token
        chat_id = self.chat_id
        message = f"Alert message {uuid.uuid4().hex}"
        
        result = send_telegram_notification(token, chat_id, message)
        self.assertTrue(result)

    def test_dispatch_portfolio_alerts_flow(self):
        expected_summary = f"Summary data {uuid.uuid4().hex}"
        expected_pnl = round(random.uniform(-500.0, 500.0), 2)

        with patch('skills.market_portfolio_monitor.run_pipeline') as mock_run_pipeline, \
             patch('skills.market_portfolio_valuation.PortfolioValuation') as mock_valuation_cls, \
             patch('skills.market_portfolio_alert_dispatcher.send_telegram_notification') as mock_send_tg:

            mock_valuation_instance = mock_valuation_cls.return_value
            mock_valuation_instance.get_total_summary.return_value = expected_summary
            mock_valuation_instance.calculate_portfolio_pnl.return_value = expected_pnl

            result = dispatch_portfolio_alerts(
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.storage_file
            )

            mock_run_pipeline.assert_called_once_with(
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.storage_file
            )
            mock_valuation_cls.assert_called_once_with(storage_file=self.storage_file)
            mock_valuation_instance.get_total_summary.assert_called_once_with(self.url)
            mock_valuation_instance.calculate_portfolio_pnl.assert_called_once_with(self.url)

            self.assertTrue(os.path.exists(self.storage_file))

            expected_message = f"Portfolio Alert:\n{expected_summary}\nPNL: {expected_pnl}"
            mock_send_tg.assert_called_once_with(
                self.telegram_token,
                self.chat_id,
                expected_message
            )

            self.assertEqual(result["summary"], expected_summary)
            self.assertEqual(result["pnl"], expected_pnl)
            self.assertEqual(result["status"], "dispatched")

    def test_process_stream_alert_with_generator(self):
        alert_id = uuid.uuid4().hex
        mock_stream_data = f"stream_dump_{uuid.uuid4().hex}".encode('utf-8')
        mock_bytes_io = io.BytesIO(mock_stream_data)

        with patch('skills.market_portfolio_alert_dispatcher.market_report_generator') as mock_generator_mod:
            if mock_generator_mod is not None:
                mock_generator_instance = mock_generator_mod.MarketReportGenerator.return_value
                mock_generator_instance.get_raw_stream_dump.return_value = mock_bytes_io

                result = process_stream_alert(alert_id)

                mock_generator_mod.MarketReportGenerator.assert_called_once()
                mock_generator_instance.get_raw_stream_dump.assert_called_once_with(alert_id)
                self.assertEqual(result.read(), mock_stream_data)

    def test_process_stream_alert_without_generator(self):
        alert_id = uuid.uuid4().hex
        with patch('skills.market_portfolio_alert_dispatcher.market_report_generator', None):
            result = process_stream_alert(alert_id)
            self.assertIsInstance(result, io.BytesIO)
            self.assertEqual(result.read(), b"")

    def test_dispatch_portfolio_alerts_kwargs_message(self):
        with patch('skills.market_portfolio_monitor.run_pipeline'), \
             patch('skills.market_portfolio_valuation.PortfolioValuation'), \
             patch('skills.market_portfolio_alert_dispatcher.send_telegram_notification') as mock_send_tg:

            custom_msg = "Custom alert message"
            result = dispatch_portfolio_alerts(
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                message=custom_msg
            )
            mock_send_tg.assert_called_once_with(self.telegram_token, self.chat_id, custom_msg)
            self.assertEqual(result["status"], "dispatched")

    def test_process_stream_alert_dict_dump(self):
        alert_id = uuid.uuid4().hex
        mock_data = {"key": "value"}

        with patch('skills.market_portfolio_alert_dispatcher.market_report_generator') as mock_generator_mod:
            mock_generator_instance = mock_generator_mod.MarketReportGenerator.return_value
            mock_generator_instance.get_raw_stream_dump.return_value = mock_data

            result = process_stream_alert(alert_id=alert_id)
            self.assertIsInstance(result, io.BytesIO)
            self.assertIn(b"key", result.read())