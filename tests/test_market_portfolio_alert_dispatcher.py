import unittest
from unittest.mock import patch, MagicMock
import os
import io
import uuid
import random
import string

from skills import market_portfolio_alert_dispatcher
from skills import market_portfolio_monitor
from skills import market_portfolio_valuation
from skills import market_report_generator

class TestMarketPortfolioAlertDispatcher(unittest.TestCase):

    def setUp(self):
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.random_token = uuid.uuid4().hex
        self.random_chat = str(random.randint(100000, 9999999))
        self.random_storage = f"/tmp/{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_send_telegram_notification(self):
        msg = uuid.uuid4().hex
        res = market_portfolio_alert_dispatcher.send_telegram_notification(self.random_token, self.random_chat, msg)
        self.assertTrue(res)

    @patch('skills.market_portfolio_monitor.run_pipeline')
    @patch('skills.market_portfolio_valuation.PortfolioValuation')
    def test_dispatch_portfolio_alerts_success(self, mock_valuation_cls, mock_run_pipeline):
        mock_valuation_instance = MagicMock()
        rand_summary = f"Summary_{uuid.uuid4().hex[:6]}"
        rand_pnl = round(random.uniform(-1000.0, 1000.0), 2)

        mock_valuation_instance.get_total_summary.return_value = rand_summary
        mock_valuation_instance.calculate_portfolio_pnl.return_value = rand_pnl
        mock_valuation_cls.return_value = mock_valuation_instance

        with patch('skills.market_portfolio_alert_dispatcher.send_telegram_notification') as mock_send:
            result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat,
                storage_file=self.random_storage,
                severity_level="HIGH",
                min_threshold="MEDIUM",
                channels=["telegram"]
            )

            mock_run_pipeline.assert_called_once_with(
                self.random_symbol, self.random_url, self.random_token, self.random_chat, self.random_storage
            )
            mock_send.assert_called_once()
            self.assertEqual(result["summary"], rand_summary)
            self.assertEqual(result["pnl"], rand_pnl)
            self.assertEqual(result["status"], "dispatched")
            self.assertTrue(os.path.exists(self.random_storage))

    @patch('skills.market_portfolio_monitor.run_pipeline')
    def test_dispatch_portfolio_alerts_filtered_out(self, mock_run_pipeline):
        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat,
            storage_file=self.random_storage,
            severity_level="LOW",
            min_threshold="HIGH",
            channels=["telegram"]
        )

        mock_run_pipeline.assert_not_called()
        self.assertEqual(result["status"], "filtered_out")

    @patch('skills.market_report_generator.MarketReportGenerator')
    def test_process_stream_alert_success(self, mock_gen_cls):
        alert_id = uuid.uuid4().hex
        expected_output = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        mock_gen_instance = MagicMock()
        mock_gen_instance.get_raw_stream_dump.return_value = expected_output
        mock_gen_cls.return_value = mock_gen_instance

        res = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
        mock_gen_instance.get_raw_stream_dump.assert_called_with(alert_id)
        self.assertEqual(res, expected_output)

    @patch('skills.market_report_generator.MarketReportGenerator')
    def test_process_stream_alert_type_error_fallback(self, mock_gen_cls):
        alert_id = uuid.uuid4().hex
        expected_output = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        mock_gen_instance = MagicMock()
        mock_gen_instance.get_raw_stream_dump.side_effect = [TypeError, expected_output]
        mock_gen_cls.return_value = mock_gen_instance

        res = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
        self.assertEqual(res, expected_output)

    @patch('skills.market_report_generator.MarketReportGenerator')
    def test_process_stream_alert_double_type_error_empty_bytes(self, mock_gen_cls):
        alert_id = uuid.uuid4().hex

        mock_gen_instance = MagicMock()
        mock_gen_instance.get_raw_stream_dump.side_effect = TypeError
        mock_gen_cls.return_value = mock_gen_instance

        res = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
        self.assertIsInstance(res, io.BytesIO)
        self.assertEqual(res.read(), b"")

if __name__ == '__main__':
    unittest.main()