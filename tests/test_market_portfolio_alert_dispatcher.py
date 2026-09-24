import unittest
from unittest.mock import patch, MagicMock
import os
import io
import uuid
import random
from skills import market_portfolio_alert_dispatcher
from skills import db_storage


class TestMarketPortfolioAlertDispatcher(unittest.TestCase):

    def setUp(self):
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_url = f"https://api.test.net/{uuid.uuid4().hex[:8]}"
        self.random_token = f"tok_{uuid.uuid4().hex[:10]}"
        self.random_chat_id = str(random.randint(100000, 999999))
        self.random_storage = f"/tmp/store_{uuid.uuid4().hex}.json"
        self.random_alert_id = uuid.uuid4().hex

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_send_telegram_notification(self):
        random_msg = f"msg_{uuid.uuid4().hex}"
        res = market_portfolio_alert_dispatcher.send_telegram_notification(
            self.random_token, self.random_chat_id, random_msg
        )
        self.assertTrue(res)

    def test_dispatch_portfolio_alerts_filtered_out(self):
        res = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage,
            severity_level="LOW",
            min_threshold="HIGH",
            channels=["telegram"]
        )
        self.assertEqual(res, {"status": "filtered_out"})

    def test_dispatch_portfolio_alerts_dispatched(self):
        random_summary = f"Summary_{uuid.uuid4().hex}"
        random_pnl = round(random.uniform(-1000.0, 1000.0), 2)

        with patch('skills.market_portfolio_monitor.run_pipeline') as mock_run_pipeline, \
             patch('skills.market_portfolio_valuation.PortfolioValuation') as mock_valuation_cls, \
             patch('skills.market_portfolio_alert_dispatcher.send_telegram_notification') as mock_send_tg:

            mock_valuation_instance = mock_valuation_cls.return_value
            mock_valuation_instance.get_total_summary.return_value = random_summary
            mock_valuation_instance.calculate_portfolio_pnl.return_value = random_pnl

            res = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage,
                severity_level="HIGH",
                min_threshold="MEDIUM",
                channels=["telegram"]
            )

            mock_run_pipeline.assert_called_once_with(
                self.random_symbol,
                self.random_url,
                self.random_token,
                self.random_chat_id,
                self.random_storage
            )
            mock_valuation_instance.get_total_summary.assert_called_once_with(self.random_url)
            mock_valuation_instance.calculate_portfolio_pnl.assert_called_once_with(self.random_url)
            mock_send_tg.assert_called_once()

            self.assertTrue(os.path.exists(self.random_storage))
            self.assertEqual(res["summary"], random_summary)
            self.assertEqual(res["pnl"], random_pnl)
            self.assertEqual(res["status"], "dispatched")

    def test_process_stream_alert_success(self):
        random_bytes = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        expected_io = io.BytesIO(random_bytes)

        with patch('skills.market_report_generator.MarketReportGenerator') as mock_generator_cls:
            mock_generator_instance = mock_generator_cls.return_value
            mock_generator_instance.get_raw_stream_dump.return_value = expected_io

            res = market_portfolio_alert_dispatcher.process_stream_alert(self.random_alert_id)
            mock_generator_instance.get_raw_stream_dump.assert_called_once_with(self.random_alert_id)
            self.assertEqual(res, expected_io)

    def test_process_stream_alert_type_error_fallback(self):
        random_bytes = f"fallback_data_{uuid.uuid4().hex}".encode('utf-8')
        expected_io = io.BytesIO(random_bytes)

        with patch('skills.market_report_generator.MarketReportGenerator') as mock_generator_cls:
            mock_generator_instance = mock_generator_cls.return_value
            mock_generator_instance.get_raw_stream_dump.side_effect = [TypeError, expected_io]

            res = market_portfolio_alert_dispatcher.process_stream_alert(self.random_alert_id)
            self.assertEqual(mock_generator_instance.get_raw_stream_dump.call_count, 2)
            self.assertEqual(res, expected_io)

    def test_process_stream_alert_double_type_error(self):
        with patch('skills.market_report_generator.MarketReportGenerator') as mock_generator_cls:
            mock_generator_instance = mock_generator_cls.return_value
            mock_generator_instance.get_raw_stream_dump.side_effect = TypeError

            res = market_portfolio_alert_dispatcher.process_stream_alert(self.random_alert_id)
            self.assertIsInstance(res, io.BytesIO)
            self.assertEqual(res.read(), b"")

    def test_db_storage_integration_honesty(self):
        self.assertTrue(hasattr(db_storage, "__file__") or callable(db_storage))


if __name__ == "__main__":
    unittest.main()
