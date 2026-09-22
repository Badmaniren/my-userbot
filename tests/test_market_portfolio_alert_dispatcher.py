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
        self.random_suffix = uuid.uuid4().hex[:8]
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        self.url = f"https://example.com/market/{self.random_suffix}"
        self.token = f"{random.randint(100000, 999999)}:AAF{uuid.uuid4().hex[:20]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.storage_file = f"test_storage_{self.random_suffix}.json"
        self.alert_id = uuid.uuid4().hex

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        dir_name = os.path.dirname(os.path.abspath(self.storage_file))
        if dir_name and os.path.exists(dir_name) and not os.listdir(dir_name):
            try:
                os.rmdir(dir_name)
            except OSError:
                pass

    def test_send_telegram_notification_returns_true(self):
        random_msg = f"Alert message {uuid.uuid4().hex}"
        result = market_portfolio_alert_dispatcher.send_telegram_notification(
            self.token, self.chat_id, random_msg
        )
        self.assertTrue(result)

    def test_dispatch_portfolio_alerts_execution_flow(self):
        expected_summary = f"Summary data {uuid.uuid4().hex}"
        expected_pnl = round(random.uniform(-5000.0, 5000.0), 2)

        with patch("skills.market_portfolio_monitor.run_pipeline") as mock_run_pipeline, \
             patch("skills.market_portfolio_valuation.PortfolioValuation") as mock_valuation_cls, \
             patch("skills.market_portfolio_alert_dispatcher.send_telegram_notification") as mock_send_tg:

            mock_valuation_instance = mock_valuation_cls.return_value
            mock_valuation_instance.get_total_summary.return_value = expected_summary
            mock_valuation_instance.calculate_portfolio_pnl.return_value = expected_pnl

            result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
                self.symbol, self.url, self.token, self.chat_id, self.storage_file
            )

            mock_run_pipeline.assert_called_once_with(
                self.symbol, self.url, self.token, self.chat_id, self.storage_file
            )
            mock_valuation_cls.assert_called_once_with(storage_file=self.storage_file)
            mock_valuation_instance.get_total_summary.assert_called_once_with(self.url)
            mock_valuation_instance.calculate_portfolio_pnl.assert_called_once_with(self.url)

            self.assertTrue(os.path.exists(self.storage_file))

            expected_message = f"Portfolio Alert:\n{expected_summary}\nPNL: {expected_pnl}"
            mock_send_tg.assert_called_once_with(self.token, self.chat_id, expected_message)

            self.assertEqual(result["summary"], expected_summary)
            self.assertEqual(result["pnl"], expected_pnl)
            self.assertEqual(result["status"], "dispatched")

    def test_dispatch_portfolio_alerts_creates_storage_if_missing(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

        with patch("skills.market_portfolio_monitor.run_pipeline"), \
             patch("skills.market_portfolio_valuation.PortfolioValuation") as mock_valuation_cls, \
             patch("skills.market_portfolio_alert_dispatcher.send_telegram_notification"):

            mock_valuation_instance = mock_valuation_cls.return_value
            mock_valuation_instance.get_total_summary.return_value = "Random Summary"
            mock_valuation_instance.calculate_portfolio_pnl.return_value = 0.0

            market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
                self.symbol, self.url, self.token, self.chat_id, self.storage_file
            )

            self.assertTrue(os.path.exists(self.storage_file))
            with open(self.storage_file, "r") as f:
                content = f.read()
            self.assertEqual(content, "{}")

    def test_process_stream_alert_with_generator(self):
        random_bytes = uuid.uuid4().bytes
        mock_generator_instance = MagicMock()
        mock_generator_instance.get_raw_stream_dump.return_value = io.BytesIO(random_bytes)

        if market_portfolio_alert_dispatcher.market_report_generator is not None:
            with patch("skills.market_report_generator.MarketReportGenerator", return_value=mock_generator_instance):
                stream = market_portfolio_alert_dispatcher.process_stream_alert(self.alert_id)
                self.assertIsInstance(stream, io.BytesIO)
                self.assertEqual(stream.read(), random_bytes)
        else:
            with patch("skills.market_report_generator", create=True) as mock_report_gen_module:
                mock_report_gen_module.MarketReportGenerator.return_value = mock_generator_instance
                original_generator = market_portfolio_alert_dispatcher.market_report_generator
                market_portfolio_alert_dispatcher.market_report_generator = mock_report_gen_module
                try:
                    stream = market_portfolio_alert_dispatcher.process_stream_alert(self.alert_id)
                    self.assertIsInstance(stream, io.BytesIO)
                    self.assertEqual(stream.read(), random_bytes)
                finally:
                    market_portfolio_alert_dispatcher.market_report_generator = original_generator

    def test_process_stream_alert_without_generator(self):
        original_generator = market_portfolio_alert_dispatcher.market_report_generator
        market_portfolio_alert_dispatcher.market_report_generator = None
        try:
            stream = market_portfolio_alert_dispatcher.process_stream_alert(self.alert_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), b"")
        finally:
            market_portfolio_alert_dispatcher.market_report_generator = original_generator

if __name__ == "__main__":
    unittest.main()