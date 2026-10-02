import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_portfolio_autonomous_sentinel import AutonomousSentinel, run_autonomous_sentinel


class TestAutonomousSentinel(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/api/v1/market"
        self.random_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        self.random_chat_id = str(random.randint(1000000, 99999999))
        self.random_threshold = round(random.uniform(1.0, 10.0), 2)
        self.random_price = round(random.uniform(50.0, 5000.0), 2)

    def test_sentinel_initialization(self):
        sentinel = AutonomousSentinel(storage_file=self.random_storage, threshold=self.random_threshold)
        self.assertEqual(sentinel.storage_file, self.random_storage)
        self.assertEqual(sentinel.threshold, self.random_threshold)

    @patch('skills.market_portfolio_autonomous_sentinel.MarketParser')
    @patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator')
    @patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts')
    def test_surveillance_below_threshold(self, mock_dispatch, mock_aggregator_cls, mock_parser_cls):
        mock_parser = mock_parser_cls.return_value
        mock_parser.fetch_price.return_value = self.random_price

        mock_aggregator = mock_aggregator_cls.return_value
        small_shift = self.random_threshold / 2.0
        mock_aggregator.build_predictive_forecast.return_value = {
            'forecast': self.random_price + 1.0,
            'percentage_shift': small_shift
        }

        sentinel = AutonomousSentinel(storage_file=self.random_storage, threshold=self.random_threshold)
        result = sentinel.run_surveillance(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id
        )

        self.assertEqual(result["status"], "stable")
        self.assertFalse(bool(result))
        mock_dispatch.assert_not_called()

    @patch('skills.market_portfolio_autonomous_sentinel.MarketParser')
    @patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator')
    @patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts')
    def test_surveillance_above_threshold_triggers_alert(self, mock_dispatch, mock_aggregator_cls, mock_parser_cls):
        mock_parser = mock_parser_cls.return_value
        mock_parser.fetch_market_data.return_value = self.random_price

        mock_aggregator = mock_aggregator_cls.return_value
        large_shift = self.random_threshold + round(random.uniform(1.0, 5.0), 2)
        mock_aggregator.build_predictive_forecast.return_value = {
            'forecast': self.random_price * 1.5,
            'percentage_shift': large_shift
        }

        sentinel = AutonomousSentinel(storage_file=self.random_storage, threshold=self.random_threshold)
        result = sentinel.run_surveillance(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id
        )

        self.assertEqual(result["status"], "triggered")
        self.assertTrue(bool(result))
        mock_dispatch.assert_called_once()

        called_kwargs = mock_dispatch.call_args[1]
        self.assertEqual(called_kwargs['telegram_token'], self.random_token)
        self.assertEqual(called_kwargs['chat_id'], self.random_chat_id)
        self.assertIn(self.random_symbol, called_kwargs['message'])
        self.assertIn(str(self.random_price), called_kwargs['message'])

    @patch('skills.market_portfolio_autonomous_sentinel.MarketParser')
    @patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator')
    @patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts')
    def test_run_autonomous_sentinel_wrapper(self, mock_dispatch, mock_aggregator_cls, mock_parser_cls):
        mock_parser = mock_parser_cls.return_value
        del mock_parser.fetch_price
        del mock_parser.fetch_market_data

        mock_aggregator = mock_aggregator_cls.return_value
        mock_aggregator.build_predictive_forecast.side_effect = TypeError("Signature mismatch")

        class DummyForecast:
            def __init__(self, f_val, s_val):
                self.forecast = f_val
                self.percentage_shift = s_val

        mock_aggregator.build_predictive_forecast.return_value = DummyForecast(self.random_price, self.random_threshold + 5.0)

        result = run_autonomous_sentinel(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage,
            threshold=self.random_threshold
        )

        self.assertEqual(result["status"], "triggered")
        self.assertTrue(bool(result))
        mock_dispatch.assert_called_once()


if __name__ == '__main__':
    unittest.main()