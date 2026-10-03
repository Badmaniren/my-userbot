import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_portfolio_autonomous_sentinel import AutonomousSentinel, run_autonomous_sentinel


class TestAutonomousSentinel(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"storage_{self.random_suffix}.json"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        self.url = f"https://{uuid.uuid4().hex[:6]}.market/{uuid.uuid4().hex[:6]}"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:20]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.threshold = float(random.randint(1, 10))

    def test_sentinel_initialization(self):
        sentinel = AutonomousSentinel(storage_file=self.storage_file, threshold=self.threshold)
        self.assertEqual(sentinel.storage_file, self.storage_file)
        self.assertEqual(sentinel.threshold, self.threshold)

    @patch('skills.market_portfolio_autonomous_sentinel.MarketParser')
    @patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator')
    @patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts')
    def test_run_surveillance_triggered(self, mock_dispatch, mock_aggregator_cls, mock_parser_cls):
        mock_parser = MagicMock()
        expected_price = round(random.uniform(50.0, 500.0), 2)
        mock_parser.fetch_price.return_value = expected_price
        mock_parser_cls.return_value = mock_parser

        mock_aggregator = MagicMock()
        high_shift = self.threshold + round(random.uniform(1.0, 10.0), 2)
        forecast_val = expected_price + high_shift
        mock_aggregator.build_predictive_forecast.return_value = {
            'forecast': forecast_val,
            'percentage_shift': high_shift
        }
        mock_aggregator_cls.return_value = mock_aggregator

        sentinel = AutonomousSentinel(storage_file=self.storage_file, threshold=self.threshold)
        result = sentinel.run_surveillance(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        self.assertEqual(result["status"], "triggered")
        self.assertTrue(result)
        mock_dispatch.assert_called_once()
        called_args, called_kwargs = mock_dispatch.call_args
        self.assertEqual(called_kwargs['telegram_token'], self.telegram_token)
        self.assertEqual(called_kwargs['chat_id'], self.chat_id)
        self.assertIn(self.symbol, called_kwargs['message'])

    @patch('skills.market_portfolio_autonomous_sentinel.MarketParser')
    @patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator')
    @patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts')
    def test_run_surveillance_stable(self, mock_dispatch, mock_aggregator_cls, mock_parser_cls):
        mock_parser = MagicMock()
        expected_price = round(random.uniform(10.0, 100.0), 2)
        del mock_parser.fetch_price
        mock_parser.fetch_market_data.return_value = expected_price
        mock_parser_cls.return_value = mock_parser

        mock_aggregator = MagicMock()
        low_shift = round(random.uniform(0.0, self.threshold - 0.1), 2)
        mock_aggregator.build_predictive_forecast.return_value = {
            'forecast': expected_price,
            'percentage_shift': low_shift
        }
        mock_aggregator_cls.return_value = mock_aggregator

        sentinel = AutonomousSentinel(storage_file=self.storage_file, threshold=self.threshold)
        result = sentinel.run_surveillance(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        self.assertEqual(result["status"], "stable")
        self.assertFalse(result)
        mock_dispatch.assert_not_called()

    @patch('skills.market_portfolio_autonomous_sentinel.MarketParser')
    @patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator')
    @patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts')
    def test_predictive_aggregator_typeerror_fallback_chains(self, mock_dispatch, mock_aggregator_cls, mock_parser_cls):
        mock_parser = MagicMock()
        del mock_parser.fetch_price
        del mock_parser.fetch_market_data
        mock_parser_cls.return_value = mock_parser

        mock_aggregator = MagicMock()
        mock_aggregator.build_predictive_forecast.side_effect = [
            TypeError("Too many arguments with url and shift"),
            TypeError("Too many arguments with url"),
            {'forecast': 150.0, 'percentage_shift': 0.0}
        ]
        mock_aggregator_cls.return_value = mock_aggregator

        sentinel = AutonomousSentinel(storage_file=self.storage_file, threshold=self.threshold)
        result = sentinel.run_surveillance(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        self.assertEqual(result["status"], "stable")
        self.assertEqual(mock_aggregator.build_predictive_forecast.call_count, 3)

    @patch('skills.market_portfolio_autonomous_sentinel.MarketParser')
    @patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator')
    @patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts')
    def test_run_autonomous_sentinel_helper_function(self, mock_dispatch, mock_aggregator_cls, mock_parser_cls):
        mock_parser = MagicMock()
        price = round(random.uniform(100.0, 200.0), 2)
        mock_parser.fetch_price.return_value = price
        mock_parser_cls.return_value = mock_parser

        mock_aggregator = MagicMock()
        mock_aggregator.build_predictive_forecast.return_value = {
            'forecast': price,
            'percentage_shift': 0.0
        }
        mock_aggregator_cls.return_value = mock_aggregator

        result = run_autonomous_sentinel(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            threshold=self.threshold
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "stable")


if __name__ == '__main__':
    unittest.main()