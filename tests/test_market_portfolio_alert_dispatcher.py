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
        self.url = f"https://{uuid.uuid4().hex[:8]}.org/api/v1"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:10]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_send_telegram_notification(self):
        msg = f"Alert message {uuid.uuid4().hex}"
        res = market_portfolio_alert_dispatcher.send_telegram_notification(
            self.telegram_token, self.chat_id, msg
        )
        self.assertTrue(res)

    def test_dispatch_portfolio_alerts_filtered_out(self):
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        severity_level = "LOW"
        min_threshold = "HIGH"

        res = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=severity_level,
            min_threshold=min_threshold
        )

        self.assertEqual(res.get("status"), "filtered_out")

    @patch("skills.market_portfolio_alert_dispatcher.market_portfolio_monitor")
    @patch("skills.market_portfolio_alert_dispatcher.market_portfolio_valuation")
    @patch("skills.market_portfolio_alert_dispatcher.send_telegram_notification")
    def test_dispatch_portfolio_alerts_success(self, mock_send_tg, mock_valuation, mock_monitor):
        expected_summary = f"Summary_{uuid.uuid4().hex}"
        expected_pnl = round(random.uniform(-5000.0, 5000.0), 2)

        valuation_instance_mock = MagicMock()
        valuation_instance_mock.get_total_summary.return_value = expected_summary
        valuation_instance_mock.calculate_portfolio_pnl.return_value = expected_pnl
        mock_valuation.PortfolioValuation.return_value = valuation_instance_mock

        mock_send_tg.return_value = True

        res = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level="CRITICAL",
            min_threshold="LOW",
            channels=["telegram"]
        )

        mock_monitor.run_pipeline.assert_called_once_with(
            self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
        )
        valuation_instance_mock.get_total_summary.assert_called_once_with(self.url)
        valuation_instance_mock.calculate_portfolio_pnl.assert_called_once_with(self.url)
        mock_send_tg.assert_called_once()

        self.assertEqual(res["summary"], expected_summary)
        self.assertEqual(res["pnl"], expected_pnl)
        self.assertEqual(res["status"], "dispatched")
        self.assertTrue(os.path.exists(self.storage_file))

    @patch("skills.market_portfolio_alert_dispatcher.market_report_generator")
    def test_process_stream_alert_success(self, mock_report_generator):
        alert_id = uuid.uuid4().hex
        expected_bytes = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        
        generator_instance_mock = MagicMock()
        generator_instance_mock.get_raw_stream_dump.return_value = io.BytesIO(expected_bytes)
        mock_report_generator.MarketReportGenerator.return_value = generator_instance_mock

        result_stream = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
        
        self.assertIsInstance(result_stream, io.BytesIO)
        self.assertEqual(result_stream.read(), expected_bytes)

    @patch("skills.market_portfolio_alert_dispatcher.market_report_generator")
    def test_process_stream_alert_type_error_fallback(self, mock_report_generator):
        alert_id = uuid.uuid4().hex
        expected_bytes = f"fallback_data_{uuid.uuid4().hex}".encode('utf-8')

        generator_instance_mock = MagicMock()
        
        def side_effect(arg=None):
            if arg is not None:
                raise TypeError("No args allowed")
            return io.BytesIO(expected_bytes)

        generator_instance_mock.get_raw_stream_dump.side_effect = side_effect
        mock_report_generator.MarketReportGenerator.return_value = generator_instance_mock

        result_stream = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)

        self.assertIsInstance(result_stream, io.BytesIO)
        self.assertEqual(result_stream.read(), expected_bytes)

    @patch("skills.market_portfolio_alert_dispatcher.market_report_generator")
    def test_process_stream_alert_general_exception(self, mock_report_generator):
        alert_id = uuid.uuid4().hex

        generator_instance_mock = MagicMock()
        generator_instance_mock.get_raw_stream_dump.side_effect = Exception("Critical stream failure")
        mock_report_generator.MarketReportGenerator.return_value = generator_instance_mock

        result_stream = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)

        self.assertIsInstance(result_stream, io.BytesIO)
        self.assertEqual(result_stream.read(), b"")

    @patch("skills.market_portfolio_alert_dispatcher.market_report_generator", None)
    def test_process_stream_alert_no_generator(self):
        alert_id = uuid.uuid4().hex
        result_stream = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
        self.assertIsInstance(result_stream, io.BytesIO)
        self.assertEqual(result_stream.read(), b"")


if __name__ == "__main__":
    unittest.main()