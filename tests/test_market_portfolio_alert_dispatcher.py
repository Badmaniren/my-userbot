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
        self.url = f"https://api.{uuid.uuid4().hex[:8]}.com/v1/portfolio"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.storage_file = os.path.join("tmp", f"store_{uuid.uuid4().hex}.json")

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
                os.rmdir(os.path.dirname(os.path.abspath(self.storage_file)))
            except OSError:
                pass

    def test_send_telegram_notification(self):
        rand_msg = ''.join(random.choices(string.ascii_letters + string.digits, k=25))
        result = market_portfolio_alert_dispatcher.send_telegram_notification(
            self.telegram_token, self.chat_id, rand_msg
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

    def test_dispatch_portfolio_alerts_dispatched(self):
        expected_summary = f"Summary_{uuid.uuid4().hex[:8]}"
        expected_pnl = float(random.randint(-5000, 5000)) + random.random()
        
        with patch("skills.market_portfolio_alert_dispatcher.market_portfolio_monitor.run_pipeline") as mock_monitor, \
             patch("skills.market_portfolio_alert_dispatcher.market_portfolio_valuation.PortfolioValuation") as mock_val_cls, \
             patch("skills.market_portfolio_alert_dispatcher.send_telegram_notification") as mock_send_tg:
            
            mock_valuation_instance = MagicMock()
            mock_valuation_instance.get_total_summary.return_value = expected_summary
            mock_valuation_instance.calculate_portfolio_pnl.return_value = expected_pnl
            mock_val_cls.return_value = mock_valuation_instance

            result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file,
                severity_level="CRITICAL",
                min_threshold="MEDIUM",
                channels=["telegram"]
            )

            mock_monitor.assert_called_once_with(
                self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
            )
            mock_valuation_instance.get_total_summary.assert_called_once_with(self.url)
            mock_valuation_instance.calculate_portfolio_pnl.assert_called_once_with(self.url)
            mock_send_tg.assert_called_once()
            
            self.assertEqual(result["summary"], expected_summary)
            self.assertEqual(result["pnl"], expected_pnl)
            self.assertEqual(result["status"], "dispatched")
            self.assertTrue(os.path.exists(self.storage_file))

    def test_process_stream_alert_with_generator(self):
        alert_id = uuid.uuid4().hex
        random_bytes = bytes(random.getrandbits(8) for _ in range(64))
        mock_bytes_io = io.BytesIO(random_bytes)

        if market_portfolio_alert_dispatcher.market_report_generator is not None:
            with patch("skills.market_report_generator.MarketReportGenerator") as mock_gen_cls:
                mock_generator = MagicMock()
                mock_generator.get_raw_stream_dump.return_value = mock_bytes_io
                mock_gen_cls.return_value = mock_generator

                res = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
                self.assertEqual(res.read(), random_bytes)
        else:
            res = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
            self.assertIsInstance(res, io.BytesIO)

    def test_process_stream_alert_type_error_fallback(self):
        alert_id = uuid.uuid4().hex
        random_bytes_fallback = bytes(random.getrandbits(8) for _ in range(32))
        mock_bytes_io = io.BytesIO(random_bytes_fallback)

        with patch("skills.market_portfolio_alert_dispatcher.market_report_generator") as mock_module:
            if mock_module is not None:
                mock_gen_instance = MagicMock()
                mock_gen_instance.get_raw_stream_dump.side_effect = [TypeError("First fail"), mock_bytes_io]
                mock_module.MarketReportGenerator.return_value = mock_gen_instance

                res = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
                self.assertEqual(res.read(), random_bytes_fallback)

if __name__ == "__main__":
    unittest.main()