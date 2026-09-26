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
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api/v1/market"
        self.telegram_token = f"{random.randint(1000, 9999)}:ABC-{uuid.uuid4().hex[:6]}"
        self.chat_id = f"-{random.randint(1000000, 9999999)}"
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.json"
        self.alert_id = uuid.uuid4().hex

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
        min_threshold = "HIGH"
        current_severity = "LOW"

        res = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=current_severity,
            min_threshold=min_threshold,
            channels=["telegram"]
        )
        self.assertEqual(res.get("status"), "filtered_out")

    @patch("skills.market_portfolio_monitor.run_pipeline")
    @patch("skills.market_portfolio_valuation.PortfolioValuation")
    def test_dispatch_portfolio_alerts_dispatched(self, mock_valuation_cls, mock_run_pipeline):
        mock_valuation_instance = MagicMock()
        expected_summary = f"Summary_{uuid.uuid4().hex}"
        expected_pnl = round(random.uniform(-1000.0, 1000.0), 2)

        mock_valuation_instance.get_total_summary.return_value = expected_summary
        mock_valuation_instance.calculate_portfolio_pnl.return_value = expected_pnl
        mock_valuation_cls.return_value = mock_valuation_instance

        res = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level="HIGH",
            min_threshold="MEDIUM",
            channels=["telegram"]
        )

        mock_run_pipeline.assert_called_once_with(
            self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
        )
        self.assertTrue(os.path.exists(self.storage_file))
        self.assertEqual(res.get("status"), "dispatched")
        self.assertEqual(res.get("summary"), expected_summary)
        self.assertEqual(res.get("pnl"), expected_pnl)

    def test_process_stream_alert_generator_none(self):
        with patch("skills.market_portfolio_alert_dispatcher.market_report_generator", None):
            stream = market_portfolio_alert_dispatcher.process_stream_alert(self.alert_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), b"")

    def test_process_stream_alert_success_with_id(self):
        mock_gen_module = MagicMock()
        mock_instance = MagicMock()
        expected_bytes = uuid.uuid4().hex.encode('utf-8')
        mock_instance.get_raw_stream_dump.return_value = io.BytesIO(expected_bytes)
        mock_gen_module.MarketReportGenerator.return_value = mock_instance

        with patch("skills.market_portfolio_alert_dispatcher.market_report_generator", mock_gen_module):
            stream = market_portfolio_alert_dispatcher.process_stream_alert(self.alert_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), expected_bytes)
            mock_instance.get_raw_stream_dump.assert_called_once_with(self.alert_id)

    def test_process_stream_alert_fallback_no_args(self):
        mock_gen_module = MagicMock()
        mock_instance = MagicMock()
        expected_bytes = uuid.uuid4().hex.encode('utf-8')

        def side_effect(arg=None):
            if arg is not None:
                raise TypeError("Unexpected argument")
            return io.BytesIO(expected_bytes)

        mock_instance.get_raw_stream_dump.side_effect = side_effect
        mock_gen_module.MarketReportGenerator.return_value = mock_instance

        with patch("skills.market_portfolio_alert_dispatcher.market_report_generator", mock_gen_module):
            stream = market_portfolio_alert_dispatcher.process_stream_alert(self.alert_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), expected_bytes)
            self.assertEqual(mock_instance.get_raw_stream_dump.call_count, 2)

    def test_process_stream_alert_fallback_empty_bytes(self):
        mock_gen_module = MagicMock()
        mock_instance = MagicMock()
        mock_instance.get_raw_stream_dump.side_effect = TypeError("Always fail")
        mock_gen_module.MarketReportGenerator.return_value = mock_instance

        with patch("skills.market_portfolio_alert_dispatcher.market_report_generator", mock_gen_module):
            stream = market_portfolio_alert_dispatcher.process_stream_alert(self.alert_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), b"")

    def test_alert_dispatcher_classes_and_instance(self):
        dispatcher = market_portfolio_alert_dispatcher.AlertDispatcher()
        res = dispatcher.dispatch(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertEqual(res.get("status"), "dispatched")

        mp_dispatcher = market_portfolio_alert_dispatcher.MarketPortfolioAlertDispatcher()
        res_mp = mp_dispatcher.dispatch(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            request_id=self.alert_id
        )
        self.assertEqual(res_mp.get("status"), "dispatched")
        sent = mp_dispatcher.get_sent_alerts_by_request(self.alert_id)
        self.assertEqual(len(sent), 1)
        self.assertEqual(len(mp_dispatcher.get_sent_alerts_by_request()), 1)

    @patch("skills.market_portfolio_monitor.run_pipeline")
    def test_dispatch_portfolio_alerts_exception_raised(self, mock_run_pipeline):
        mock_run_pipeline.side_effect = ValueError("Monitor failed")
        with self.assertRaises(ValueError):
            market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )


if __name__ == "__main__":
    unittest.main()