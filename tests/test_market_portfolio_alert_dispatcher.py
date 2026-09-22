import os
import io
import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string

from skills.market_portfolio_alert_dispatcher import (
    send_telegram_notification,
    dispatch_portfolio_alerts,
    process_stream_alert
)

class TestMarketPortfolioAlertDispatcher(unittest.TestCase):

    def test_send_telegram_notification(self):
        token_rand = uuid.uuid4().hex
        chat_id_rand = str(random.randint(100000, 999999))
        message_rand = "".join(random.choices(string.ascii_letters + string.digits, k=15))

        res = send_telegram_notification(token_rand, chat_id_rand, message_rand)
        self.assertTrue(res)

    def test_dispatch_portfolio_alerts_success(self):
        symbol_rand = "".join(random.choices(string.ascii_uppercase, k=4))
        url_rand = f"http://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        token_rand = uuid.uuid4().hex
        chat_id_rand = str(random.randint(10000, 99999))
        storage_file_rand = f"storage_{uuid.uuid4().hex}.json"

        expected_summary = {"data": uuid.uuid4().hex}
        expected_pnl = float(random.randint(-1000, 1000))

        with patch("skills.market_portfolio_monitor.run_pipeline") as mock_monitor, \
             patch("skills.market_portfolio_valuation.PortfolioValuation") as mock_valuation_cls, \
             patch("skills.market_portfolio_alert_dispatcher.send_telegram_notification") as mock_send_tg:

            mock_valuation_instance = MagicMock()
            mock_valuation_instance.get_total_summary.return_value = expected_summary
            mock_valuation_instance.calculate_portfolio_pnl.return_value = expected_pnl
            mock_valuation_cls.return_value = mock_valuation_instance

            result = dispatch_portfolio_alerts(
                symbol=symbol_rand,
                url=url_rand,
                telegram_token=token_rand,
                chat_id=chat_id_rand,
                storage_file=storage_file_rand,
                severity_level="HIGH",
                channels=["telegram"]
            )

            mock_monitor.assert_called_once_with(symbol_rand, url_rand, token_rand, chat_id_rand, storage_file_rand)
            mock_valuation_cls.assert_called_once_with(storage_file=storage_file_rand)
            mock_valuation_instance.get_total_summary.assert_called_once_with(url_rand)
            mock_valuation_instance.calculate_portfolio_pnl.assert_called_once_with(url_rand)
            mock_send_tg.assert_called_once()

            self.assertEqual(result["summary"], expected_summary)
            self.assertEqual(result["pnl"], expected_pnl)
            self.assertEqual(result["status"], "dispatched")

            if os.path.exists(storage_file_rand):
                os.remove(storage_file_rand)

    def test_dispatch_portfolio_alerts_filtering_severity(self):
        symbol_rand = "".join(random.choices(string.ascii_uppercase, k=3))
        url_rand = f"http://{uuid.uuid4().hex}.org"
        token_rand = uuid.uuid4().hex
        chat_id_rand = str(random.randint(100, 999))
        storage_file_rand = f"storage_{uuid.uuid4().hex}.json"

        with patch("skills.market_portfolio_monitor.run_pipeline") as mock_monitor, \
             patch("skills.market_portfolio_valuation.PortfolioValuation") as mock_valuation_cls, \
             patch("skills.market_portfolio_alert_dispatcher.send_telegram_notification") as mock_send_tg:

            result = dispatch_portfolio_alerts(
                symbol=symbol_rand,
                url=url_rand,
                telegram_token=token_rand,
                chat_id=chat_id_rand,
                storage_file=storage_file_rand,
                severity_level="LOW",
                min_threshold="HIGH",
                channels=["telegram"]
            )

            mock_monitor.assert_not_called()
            mock_valuation_cls.assert_not_called()
            mock_send_tg.assert_not_called()

            self.assertEqual(result["status"], "filtered_out")

            if os.path.exists(storage_file_rand):
                os.remove(storage_file_rand)

    def test_dispatch_portfolio_alerts_custom_channels(self):
        symbol_rand = "".join(random.choices(string.ascii_uppercase, k=5))
        url_rand = f"http://{uuid.uuid4().hex}.net"
        token_rand = uuid.uuid4().hex
        chat_id_rand = str(random.randint(1000, 9999))
        storage_file_rand = f"storage_{uuid.uuid4().hex}.json"

        with patch("skills.market_portfolio_monitor.run_pipeline") as mock_monitor, \
             patch("skills.market_portfolio_valuation.PortfolioValuation") as mock_valuation_cls, \
             patch("skills.market_portfolio_alert_dispatcher.send_telegram_notification") as mock_send_tg:

            mock_valuation_instance = MagicMock()
            mock_valuation_instance.get_total_summary.return_value = {}
            mock_valuation_instance.calculate_portfolio_pnl.return_value = 0.0
            mock_valuation_cls.return_value = mock_valuation_instance

            dispatch_portfolio_alerts(
                symbol=symbol_rand,
                url=url_rand,
                telegram_token=token_rand,
                chat_id=chat_id_rand,
                storage_file=storage_file_rand,
                severity_level="CRITICAL",
                channels=["webhook"]
            )

            mock_send_tg.assert_not_called()

            if os.path.exists(storage_file_rand):
                os.remove(storage_file_rand)

    def test_process_stream_alert_with_generator(self):
        alert_id_rand = uuid.uuid4().hex
        expected_bytes = uuid.uuid4().hex.encode('utf-8')

        with patch("skills.market_report_generator.MarketReportGenerator") as mock_generator_cls:
            mock_gen_instance = MagicMock()
            mock_gen_instance.get_raw_stream_dump.return_value = io.BytesIO(expected_bytes)
            mock_generator_cls.return_value = mock_gen_instance

            result = process_stream_alert(alert_id_rand)
            
            self.assertIsInstance(result, io.BytesIO)
            self.assertEqual(result.read(), expected_bytes)

    def test_process_stream_alert_fallback(self):
        alert_id_rand = uuid.uuid4().hex

        with patch("skills.market_report_generator.MarketReportGenerator") as mock_generator_cls:
            mock_gen_instance = MagicMock()
            mock_gen_instance.get_raw_stream_dump.side_effect = TypeError("Invalid arguments")
            mock_generator_cls.return_value = mock_gen_instance

            result = process_stream_alert(alert_id_rand)
            
            self.assertIsInstance(result, io.BytesIO)
            self.assertEqual(result.read(), b"")

if __name__ == "__main__":
    unittest.main()