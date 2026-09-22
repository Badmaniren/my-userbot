import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string
from skills.market_portfolio_alert_filter_aggregator import (
    MarketPortfolioAlertFilterAggregator
)


class TestMarketPortfolioAlertFilterAggregator(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex}.com/market"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:20]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.severity_level = random.choice(["INFO", "WARNING", "CRITICAL", "HIGH"])
        self.min_threshold = round(random.uniform(1.0, 100.0), 2)
        self.channels = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]
        self.percentage_shift = round(random.uniform(-15.0, 15.0), 2)
        self.aggregator = MarketPortfolioAlertFilterAggregator(self.storage_file)

    def test_init_sets_storage_file(self):
        expected_storage = f"{uuid.uuid4().hex}.json"
        instance = MarketPortfolioAlertFilterAggregator(expected_storage)
        self.assertEqual(instance.storage_file, expected_storage)

    @patch("skills.market_portfolio_alert_filter_aggregator.PredictiveAggregator")
    @patch("skills.market_portfolio_alert_filter_aggregator.dispatch_portfolio_alerts")
    def test_filter_and_dispatch_high_severity(self, mock_dispatch, mock_predictive_aggregator_cls):
        mock_aggregator_instance = mock_predictive_aggregator_cls.return_value
        expected_forecast_key = uuid.uuid4().hex
        expected_forecast_value = round(random.uniform(10.0, 500.0), 2)
        mock_aggregator_instance.build_predictive_forecast.return_value = {
            expected_forecast_key: expected_forecast_value
        }

        with patch("builtins.print") as mock_print:
            result = self.aggregator.filter_and_dispatch(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                severity_level=self.severity_level,
                min_threshold=self.min_threshold,
                channels=self.channels,
                percentage_shift=self.percentage_shift
            )

        mock_predictive_aggregator_cls.assert_called_once_with(self.storage_file)
        mock_aggregator_instance.build_predictive_forecast.assert_called_once_with(
            self.symbol, self.url, self.percentage_shift
        )
        mock_dispatch.assert_called_once()
        self.assertIsInstance(result, dict)
        self.assertIn("forecast", result)
        self.assertIn("dispatched", result)

    @patch("skills.market_portfolio_alert_filter_aggregator.PredictiveAggregator")
    @patch("skills.market_portfolio_alert_filter_aggregator.dispatch_portfolio_alerts")
    def test_filter_and_dispatch_low_severity_filters_out(self, mock_dispatch, mock_predictive_aggregator_cls):
        mock_aggregator_instance = mock_predictive_aggregator_cls.return_value
        low_forecast = round(random.uniform(0.01, 0.5), 2)
        mock_aggregator_instance.build_predictive_forecast.return_value = {
            uuid.uuid4().hex: low_forecast
        }

        result = self.aggregator.filter_and_dispatch(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level="LOW",
            min_threshold=100.0,
            channels=self.channels,
            percentage_shift=self.percentage_shift
        )

        mock_dispatch.assert_not_called()
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("filtered_out", True))

    @patch("skills.market_portfolio_alert_filter_aggregator.aggregate_market_forecast")
    def test_aggregate_and_prioritize_alerts(self, mock_aggregate_market_forecast):
        expected_agg_key = uuid.uuid4().hex
        expected_agg_val = round(random.uniform(50.0, 1000.0), 2)
        mock_aggregate_market_forecast.return_value = {
            expected_agg_key: expected_agg_val
        }

        prioritized = self.aggregator.aggregate_and_prioritize_alerts(
            symbol=self.symbol,
            url=self.url,
            percentage_shift=self.percentage_shift
        )

        mock_aggregate_market_forecast.assert_called_once_with(
            self.storage_file, self.symbol, self.url, self.percentage_shift
        )
        self.assertIsInstance(prioritized, dict)
        self.assertEqual(prioritized.get(expected_agg_key), expected_agg_val)

    @patch("skills.market_portfolio_alert_filter_aggregator.PredictiveAggregator")
    def test_stream_filter_processing_with_io_bytes(self, mock_predictive_aggregator_cls):
        random_garbage = f"STREAM_DUMP_{uuid.uuid4().hex}".encode('utf-8')
        stream_mock = io.BytesIO(random_garbage)

        mock_instance = mock_predictive_aggregator_cls.return_value
        mock_instance.build_advanced_forecast.return_value = {
            uuid.uuid4().hex: uuid.uuid4().hex
        }

        res = self.aggregator.process_stream_alert_filter(stream_mock, self.symbol, self.url)
        self.assertIsInstance(res, dict)
        self.assertTrue(len(res) > 0)


if __name__ == "__main__":
    unittest.main()