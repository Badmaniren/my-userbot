import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.market_portfolio_macro_liquidity_tracker import (
    MarketPortfolioMacroLiquidityTracker,
    market_portfolio_macro_liquidity_tracker
)


class TestMarketPortfolioMacroLiquidityTracker(unittest.TestCase):

    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.monitor_mock = MagicMock()
        self.dispatcher_mock = MagicMock()
        self.tracker = MarketPortfolioMacroLiquidityTracker(
            db_storage=self.db_storage_mock,
            monitor=self.monitor_mock,
            dispatcher=self.dispatcher_mock
        )

    def test_init_properties(self):
        rand_threshold = float(random.randint(5, 25))
        self.tracker.risk_threshold = rand_threshold
        self.assertEqual(self.tracker.risk_threshold, rand_threshold)
        self.assertEqual(self.tracker.db_storage, self.db_storage_mock)
        self.assertEqual(self.tracker.monitor, self.monitor_mock)
        self.assertEqual(self.tracker.dispatcher, self.dispatcher_mock)

    def test_fetch_and_store_macro_data(self):
        rand_url = f"https://api.{uuid.uuid4().hex}.com/macro"
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(100, 9999)
        mock_response_data = {rand_metric_key: rand_metric_val}

        with patch('skills.market_portfolio_macro_liquidity_tracker.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response_data
            mock_get.return_value = mock_resp

            result = self.tracker.fetch_and_store_macro_data(rand_url)

            mock_get.assert_called_once_with(rand_url, timeout=10)
            self.db_storage_mock.save_macro_metric.assert_called_once_with(mock_response_data)
            self.assertTrue(result)

    def test_evaluate_portfolio_macro_risk_triggered(self):
        rand_portfolio_id = uuid.uuid4().hex
        self.tracker.risk_threshold = 10.0

        with patch.object(self.tracker, '_get_current_liquidity_score', return_value=3.0):
            self.tracker.evaluate_portfolio_macro_risk(rand_portfolio_id)
            self.dispatcher_mock.send_alert.assert_called_once()
            args, _ = self.dispatcher_mock.send_alert.call_args
            self.assertIn(rand_portfolio_id, args[0])

    def test_evaluate_portfolio_macro_risk_not_triggered(self):
        rand_portfolio_id = uuid.uuid4().hex
        self.tracker.risk_threshold = 5.0

        with patch.object(self.tracker, '_get_current_liquidity_score', return_value=8.0):
            self.tracker.evaluate_portfolio_macro_risk(rand_portfolio_id)
            self.dispatcher_mock.send_alert.assert_not_called()

    def test_generate_macro_report_stream_with_storage(self):
        rand_bytes = bytes(uuid.uuid4().hex, 'utf-8')
        stream_mock = io.BytesIO(rand_bytes)
        self.db_storage_mock.get_macro_export_stream = MagicMock(return_value=stream_mock)

        result_stream = self.tracker.generate_macro_report_stream()
        self.assertEqual(result_stream.read(), rand_bytes)
        self.db_storage_mock.get_macro_export_stream.assert_called_once()

    def test_generate_macro_report_stream_without_storage_method(self):
        del self.db_storage_mock.get_macro_export_stream
        result_stream = self.tracker.generate_macro_report_stream()
        self.assertIsInstance(result_stream, io.BytesIO)
        self.assertEqual(result_stream.read(), b"")


class TestMarketPortfolioMacroLiquidityTrackerFunction(unittest.TestCase):

    def test_market_portfolio_macro_liquidity_tracker_functional(self):
        rand_id = uuid.uuid4().hex
        rand_metric = round(random.uniform(1.0, 100.0), 2)
        rand_target = f"/tmp/{uuid.uuid4().hex}.txt"

        payload = {
            "id": rand_id,
            "liquidity_metric": rand_metric,
            "export_target": rand_target
        }

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('skills.market_portfolio_macro_liquidity_tracker.db_storage', create=True) as mock_db:
                result = market_portfolio_macro_liquidity_tracker(payload)

                mock_open.assert_called_once_with(rand_target, "w")
                mock_file.write.assert_called_once_with(str(rand_metric))
                mock_db.assert_called_once()
                self.assertEqual(result, {
                    "status": "success",
                    "processed_id": rand_id
                })