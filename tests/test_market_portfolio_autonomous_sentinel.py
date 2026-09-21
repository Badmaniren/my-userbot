import unittest
from unittest.mock import patch
import uuid
import random
import string
from skills.market_portfolio_autonomous_sentinel import AutonomousSentinel, run_autonomous_sentinel


class TestAutonomousSentinel(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/market/{random.randint(100, 999)}"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        self.chat_id = f"-{random.randint(10000000, 99999999)}"
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        self.threshold = round(random.uniform(1.0, 10.0), 2)

    def test_sentinel_initialization(self):
        sentinel = AutonomousSentinel(storage_file=self.storage_file, threshold=self.threshold)
        self.assertEqual(sentinel.storage_file, self.storage_file)
        self.assertEqual(sentinel.threshold, self.threshold)

    @patch('skills.market_portfolio_autonomous_sentinel.MarketParser')
    @patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator')
    @patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts')
    def test_surveillance_triggered_anomaly(self, mock_dispatch, mock_aggregator_class, mock_parser_class):
        expected_price = round(random.uniform(50.0, 500.0), 2)
        expected_forecast = round(expected_price * 1.5, 2)
        expected_shift = round(self.threshold + random.uniform(1.0, 20.0), 2)

        mock_parser_instance = mock_parser_class.return_value
        mock_parser_instance.fetch_price.return_value = expected_price

        mock_aggregator_instance = mock_aggregator_class.return_value
        mock_aggregator_instance.build_predictive_forecast.return_value = {
            'forecast': expected_forecast,
            'percentage_shift': expected_shift
        }

        sentinel = AutonomousSentinel(storage_file=self.storage_file, threshold=self.threshold)
        result = sentinel.run_surveillance(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        self.assertTrue(bool(result))
        self.assertEqual(result["status"], "triggered")
        self.assertEqual(result["forecast"]["forecast"], expected_forecast)
        self.assertEqual(result["forecast"]["percentage_shift"], expected_shift)

        mock_parser_instance.fetch_price.assert_called_once_with(self.url)
        mock_parser_instance.fetch_and_store.assert_called_once_with(self.symbol, expected_price)
        mock_aggregator_instance.build_predictive_forecast.assert_called()
        mock_dispatch.assert_called_once()

        called_args, called_kwargs = mock_dispatch.call_args
        self.assertEqual(called_kwargs['telegram_token'], self.telegram_token)
        self.assertEqual(called_kwargs['chat_id'], self.chat_id)
        self.assertIn(self.symbol, called_kwargs['message'])
        self.assertIn(str(expected_price), called_kwargs['message'])

    @patch('skills.market_portfolio_autonomous_sentinel.MarketParser')
    @patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator')
    @patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts')
    def test_surveillance_stable_market(self, mock_dispatch, mock_aggregator_class, mock_parser_class):
        expected_price = round(random.uniform(10.0, 100.0), 2)
        expected_forecast = round(expected_price * 1.01, 2)
        expected_shift = round(self.threshold - random.uniform(0.1, self.threshold), 2)

        mock_parser_instance = mock_parser_class.return_value
        mock_parser_instance.fetch_market_data.return_value = expected_price

        mock_aggregator_instance = mock_aggregator_class.return_value
        mock_aggregator_instance.build_predictive_forecast.return_value = {
            'forecast': expected_forecast,
            'percentage_shift': expected_shift
        }

        sentinel = AutonomousSentinel(storage_file=self.storage_file, threshold=self.threshold)
        result = sentinel.run_surveillance(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        self.assertFalse(bool(result))
        self.assertEqual(result["status"], "stable")
        mock_dispatch.assert_not_called()

    @patch('skills.market_portfolio_autonomous_sentinel.MarketParser')
    @patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator')
    @patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts')
    def test_run_autonomous_sentinel_wrapper(self, mock_dispatch, mock_aggregator_class, mock_parser_class):
        expected_price = round(random.uniform(1000.0, 2000.0), 2)
        mock_parser_instance = mock_parser_class.return_value
        mock_parser_instance.fetch_price.return_value = expected_price

        mock_aggregator_instance = mock_aggregator_class.return_value
        mock_aggregator_instance.build_predictive_forecast.return_value = {
            'forecast': expected_price,
            'percentage_shift': 0.0
        }

        result = run_autonomous_sentinel(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            threshold=self.threshold
        )

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("forecast", result)


if __name__ == '__main__':
    unittest.main()