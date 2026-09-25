import unittest
from unittest.mock import patch, MagicMock
import os
import io
import uuid
import random
import string

from skills import market_portfolio_alert_dispatcher


class TestMarketPortfolioAlertDispatcher(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api/v1"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        self.chat_id = str(random.randint(1000000, 99999999))
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_send_telegram_notification(self):
        message_text = f"Alert: {uuid.uuid4().hex}"
        result = market_portfolio_alert_dispatcher.send_telegram_notification(
            self.telegram_token, self.chat_id, message_text
        )
        self.assertTrue(result)

    def test_dispatch_portfolio_alerts_filtered_out(self):
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        min_threshold = "HIGH"
        severity_level = "LOW"
        
        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=severity_level,
            min_threshold=min_threshold,
            channels=["telegram"]
        )
        self.assertEqual(result.get("status"), "filtered_out")

    @patch("skills.market_portfolio_alert_dispatcher.market_portfolio_monitor")
    @patch("skills.market_portfolio_alert_dispatcher.market_portfolio_valuation")
    @patch("skills.market_portfolio_alert_dispatcher.send_telegram_notification")
    def test_dispatch_portfolio_alerts_dispatched(self, mock_send_tg, mock_valuation_mod, mock_monitor):
        expected_summary = f"Summary_{uuid.uuid4().hex[:6]}"
        expected_pnl = round(random.uniform(-1000.0, 1000.0), 2)

        mock_valuation_instance = MagicMock()
        mock_valuation_instance.get_total_summary.return_value = expected_summary
        mock_valuation_instance.calculate_portfolio_pnl.return_value = expected_pnl
        mock_valuation_mod.PortfolioValuation.return_value = mock_valuation_instance

        mock_send_tg.return_value = True

        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level="HIGH",
            min_threshold="MEDIUM",
            channels=["telegram"]
        )

        mock_monitor.run_pipeline.assert_called_once_with(
            self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
        )
        mock_valuation_mod.PortfolioValuation.assert_called_once_with(storage_file=self.storage_file)
        mock_valuation_instance.get_total_summary.assert_called_once_with(self.url)
        mock_valuation_instance.calculate_portfolio_pnl.assert_called_once_with(self.url)
        
        mock_send_tg.assert_called_once()
        self.assertEqual(result.get("status"), "dispatched")
        self.assertEqual(result.get("summary"), expected_summary)
        self.assertEqual(result.get("pnl"), expected_pnl)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_process_stream_alert_no_generator(self):
        alert_id = uuid.uuid4().hex
        with patch("skills.market_portfolio_alert_dispatcher.market_report_generator", None):
            res = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
            self.assertIsInstance(res, io.BytesIO)
            self.assertEqual(res.read(), b"")

    def test_process_stream_alert_with_generator_success(self):
        alert_id = uuid.uuid4().hex
        expected_bytes = bytes(uuid.uuid4().hex, 'utf-8')
        
        mock_gen_instance = MagicMock()
        mock_gen_instance.get_raw_stream_dump.return_value = io.BytesIO(expected_bytes)

        mock_report_gen_module = MagicMock()
        mock_report_gen_module.MarketReportGenerator.return_value = mock_gen_instance

        with patch("skills.market_portfolio_alert_dispatcher.market_report_generator", mock_report_gen_module):
            res = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
            self.assertIsInstance(res, io.BytesIO)
            self.assertEqual(res.read(), expected_bytes)
            mock_gen_instance.get_raw_stream_dump.assert_called_once_with(alert_id)

    def test_process_stream_alert_type_error_fallback(self):
        alert_id = uuid.uuid4().hex
        expected_bytes = bytes(uuid.uuid4().hex, 'utf-8')

        mock_gen_instance = MagicMock()
        # First call with alert_id raises TypeError, second call without args succeeds
        mock_gen_instance.get_raw_stream_dump.side_effect = [TypeError("Too many args"), io.BytesIO(expected_bytes)]

        mock_report_gen_module = MagicMock()
        mock_report_gen_module.MarketReportGenerator.return_value = mock_gen_instance

        with patch("skills.market_portfolio_alert_dispatcher.market_report_generator", mock_report_gen_module):
            res = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
            self.assertIsInstance(res, io.BytesIO)
            self.assertEqual(res.read(), expected_bytes)
            self.assertEqual(mock_gen_instance.get_raw_stream_dump.call_count, 2)

    def test_process_stream_alert_double_type_error(self):
        alert_id = uuid.uuid4().hex

        mock_gen_instance = MagicMock()
        mock_gen_instance.get_raw_stream_dump.side_effect = TypeError("Persistent signature mismatch")

        mock_report_gen_module = MagicMock()
        mock_report_gen_module.MarketReportGenerator.return_value = mock_gen_instance

        with patch("skills.market_portfolio_alert_dispatcher.market_report_generator", mock_report_gen_module):
            res = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
            self.assertIsInstance(res, io.BytesIO)
            self.assertEqual(res.read(), b"")


if __name__ == "__main__":
    unittest.main()