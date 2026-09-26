import unittest
from unittest.mock import patch, MagicMock
import io
import os
import uuid
import random
from skills import market_portfolio_alert_dispatcher

class TestMarketPortfolioAlertDispatcher(unittest.TestCase):

    def test_send_telegram_notification(self):
        token = uuid.uuid4().hex
        chat_id = str(random.randint(10000, 99999))
        message = f"Alert message {uuid.uuid4().hex}"
        result = market_portfolio_alert_dispatcher.send_telegram_notification(token, chat_id, message)
        self.assertTrue(result)

    @patch('skills.market_portfolio_alert_dispatcher.market_portfolio_monitor.run_pipeline')
    @patch('skills.market_portfolio_alert_dispatcher.market_portfolio_valuation.PortfolioValuation')
    @patch('skills.market_portfolio_alert_dispatcher.send_telegram_notification')
    def test_dispatch_portfolio_alerts(self, mock_send_notification, mock_valuation_cls, mock_run_pipeline):
        symbol = uuid.uuid4().hex[:5].upper()
        url = f"https://{uuid.uuid4().hex}.com/api"
        token = uuid.uuid4().hex
        chat_id = str(random.randint(1000, 9999))
        storage_file = f"storage_{uuid.uuid4().hex}.json"

        mock_valuation_instance = mock_valuation_cls.return_value
        expected_summary = f"Summary_{uuid.uuid4().hex}"
        expected_pnl = round(random.uniform(-1000, 1000), 2)

        mock_valuation_instance.get_total_summary.return_value = expected_summary
        mock_valuation_instance.calculate_portfolio_pnl.return_value = expected_pnl

        try:
            result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
                symbol, url, token, chat_id, storage_file
            )

            mock_run_pipeline.assert_called_once_with(symbol, url, token, chat_id, storage_file)
            mock_valuation_cls.assert_called_once_with(storage_file=storage_file)
            mock_valuation_instance.get_total_summary.assert_called_once_with(url)
            mock_valuation_instance.calculate_portfolio_pnl.assert_called_once_with(url)
            mock_send_notification.assert_called_once()

            self.assertEqual(result["summary"], expected_summary)
            self.assertEqual(result["pnl"], expected_pnl)
            self.assertEqual(result["status"], "dispatched")
        finally:
            if os.path.exists(storage_file):
                try:
                    os.remove(storage_file)
                except OSError:
                    pass

    @patch('skills.market_portfolio_alert_dispatcher.market_report_generator')
    def test_process_stream_alert_success(self, mock_report_generator):
        expected_bytes = uuid.uuid4().bytes
        mock_generator_instance = mock_report_generator.MarketReportGenerator.return_value
        mock_generator_instance.get_raw_stream_dump.return_value = io.BytesIO(expected_bytes)

        alert_id = uuid.uuid4().hex
        result = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)

        mock_generator_instance.get_raw_stream_dump.assert_called_once()
        self.assertIsInstance(result, io.BytesIO)
        self.assertEqual(result.read(), expected_bytes)

    @patch('skills.market_portfolio_alert_dispatcher.market_report_generator', None)
    def test_process_stream_alert_no_generator(self):
        alert_id = uuid.uuid4().hex
        result = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
        self.assertIsInstance(result, io.BytesIO)
        self.assertEqual(result.read(), b"")

if __name__ == '__main__':
    unittest.main()