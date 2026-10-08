import os
import io
import uuid
import random
import unittest
from unittest.mock import patch

from skills import market_portfolio_alert_dispatcher
from skills import market_report_generator

class TestMarketPortfolioAlertDispatcher(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.{uuid.uuid4().hex[:8]}.org/v1/query"
        self.telegram_token = f"{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(1000000, 99999999))
        self.storage_file = os.path.join("/tmp", f"portfolio_{uuid.uuid4().hex}.json")

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_send_telegram_notification_returns_boolean(self):
        result = market_portfolio_alert_dispatcher.send_telegram_notification(
            self.telegram_token, self.chat_id, f"Msg {uuid.uuid4().hex}"
        )
        self.assertIsInstance(result, bool)

    def test_send_telegram_notification_invalid_recipients(self):
        with self.assertRaises(ValueError):
            market_portfolio_alert_dispatcher.send_telegram_notification(
                "", self.chat_id, "Test message"
            )
        with self.assertRaises(ValueError):
            market_portfolio_alert_dispatcher.send_telegram_notification(
                self.telegram_token, None, "Test message"
            )

    def test_dispatch_portfolio_alerts_recipient_validation(self):
        with self.assertRaises(ValueError):
            market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
                symbol=self.symbol,
                url=self.url,
                telegram_token="",
                chat_id=self.chat_id,
                storage_file=self.storage_file,
                channels=["telegram"]
            )

    def test_dispatch_portfolio_alerts_filtered_out(self):
        high_threshold = "CRITICAL"
        low_severity = "LOW"

        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=low_severity,
            min_threshold=high_threshold
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "filtered_out")

    def test_dispatch_portfolio_alerts_success_execution(self):
        expected_summary = f"Summary_{uuid.uuid4().hex[:6]}"
        expected_pnl = round(random.uniform(-5000.0, 5000.0), 2)

        with patch("skills.market_portfolio_monitor.run_pipeline") as mock_monitor, \
             patch("skills.market_portfolio_valuation.PortfolioValuation") as mock_valuation_cls, \
             patch("skills.market_portfolio_alert_dispatcher.send_telegram_notification") as mock_tg:

            mock_valuation_instance = mock_valuation_cls.return_value
            mock_valuation_instance.get_total_summary.return_value = expected_summary
            mock_valuation_instance.calculate_portfolio_pnl.return_value = expected_pnl

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

            mock_monitor.assert_called_once_with(
                self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
            )
            mock_valuation_instance.get_total_summary.assert_called_once_with(self.url)
            mock_valuation_instance.calculate_portfolio_pnl.assert_called_once_with(self.url)
            mock_tg.assert_called_once()

            self.assertEqual(result.get("status"), "dispatched")
            self.assertEqual(result.get("summary"), expected_summary)
            self.assertEqual(result.get("pnl"), expected_pnl)
            self.assertTrue(os.path.exists(self.storage_file))

    def test_process_stream_alert_returns_stream(self):
        random_bytes = f"data_stream_{uuid.uuid4().hex}".encode("utf-8")
        
        with patch("skills.market_report_generator.MarketReportGenerator") as mock_generator_cls:
            mock_generator_instance = mock_generator_cls.return_value
            mock_generator_instance.get_raw_stream_dump.return_value = io.BytesIO(random_bytes)

            alert_id = f"alert_{uuid.uuid4().hex[:8]}"
            result = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)

            self.assertIsInstance(result, io.BytesIO)
            content = result.read()
            self.assertEqual(content, random_bytes)

    def test_process_stream_alert_handles_type_error(self):
        random_bytes = f"fallback_stream_{uuid.uuid4().hex}".encode("utf-8")
        
        with patch("skills.market_report_generator.MarketReportGenerator") as mock_generator_cls:
            mock_generator_instance = mock_generator_cls.return_value

            def side_effect(*args, **kwargs):
                if not args and not kwargs:
                    raise TypeError("Missing alert_id argument")
                return io.BytesIO(random_bytes)

            mock_generator_instance.get_raw_stream_dump.side_effect = side_effect

            alert_id = f"alert_fallback_{uuid.uuid4().hex[:8]}"
            result = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)

            self.assertIsInstance(result, io.BytesIO)
            self.assertEqual(result.read(), random_bytes)

    def test_process_stream_alert_raises_runtime_error(self):
        with patch("skills.market_report_generator.MarketReportGenerator") as mock_generator_cls:
            mock_generator_instance = mock_generator_cls.return_value
            mock_generator_instance.get_raw_stream_dump.side_effect = Exception("Critical stream failure")

            alert_id = f"err_{uuid.uuid4().hex[:6]}"
            with self.assertRaises(RuntimeError):
                market_portfolio_alert_dispatcher.process_stream_alert(alert_id)

if __name__ == "__main__":
    unittest.main()