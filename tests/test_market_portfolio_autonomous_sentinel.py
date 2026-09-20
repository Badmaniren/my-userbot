import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_autonomous_sentinel import (
    AutonomousSentinel,
    run_autonomous_sentinel
)


class TestMarketPortfolioAutonomousSentinel(unittest.TestCase):

    def setUp(self):
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/market"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:10]}"
        self.chat_id = f"-{random.randint(10000000, 99999999)}"
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.threshold = random.uniform(1.0, 15.0)

    def test_autonomous_sentinel_initialization(self):
        sentinel = AutonomousSentinel(
            storage_file=self.storage_file,
            threshold=self.threshold
        )
        self.assertEqual(sentinel.storage_file, self.storage_file)
        self.assertEqual(sentinel.threshold, self.threshold)

    @patch('skills.market_portfolio_autonomous_sentinel.MarketParser')
    @patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator')
    @patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts')
    def test_sentinel_run_surveillance_triggers_alert(
        self,
        mock_dispatch_alerts,
        mock_predictive_aggregator_cls,
        mock_market_parser_cls
    ):
        mock_parser = mock_market_parser_cls.return_value
        random_price = round(random.uniform(100.0, 5000.0), 2)
        mock_parser.fetch_price.return_value = random_price

        mock_aggregator = mock_predictive_aggregator_cls.return_value
        forecast_val = round(random_price * (1.0 + (self.threshold * 2.0 / 100.0)), 2)
        mock_aggregator.build_predictive_forecast.return_value = {
            'forecast': forecast_val,
            'percentage_shift': self.threshold * 2.0
        }

        sentinel = AutonomousSentinel(
            storage_file=self.storage_file,
            threshold=self.threshold
        )

        result = sentinel.run_surveillance(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        self.assertTrue(result)
        mock_parser.fetch_and_store.assert_called_once_with(self.symbol, random_price)
        mock_dispatch_alerts.assert_called_once()

    @patch('skills.market_portfolio_autonomous_sentinel.MarketParser')
    @patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator')
    @patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts')
    def test_sentinel_run_surveillance_no_alert(
        self,
        mock_dispatch_alerts,
        mock_predictive_aggregator_cls,
        mock_market_parser_cls
    ):
        mock_parser = mock_market_parser_cls.return_value
        random_price = round(random.uniform(10.0, 500.0), 2)
        mock_parser.fetch_price.return_value = random_price

        mock_aggregator = mock_predictive_aggregator_cls.return_value
        forecast_val = round(random_price * 1.001, 2)
        mock_aggregator.build_predictive_forecast.return_value = {
            'forecast': forecast_val,
            'percentage_shift': 0.1
        }

        sentinel = AutonomousSentinel(
            storage_file=self.storage_file,
            threshold=self.threshold
        )

        result = sentinel.run_surveillance(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        self.assertFalse(result)
        mock_parser.fetch_and_store.assert_called_once_with(self.symbol, random_price)
        mock_dispatch_alerts.assert_not_called()

    @patch('skills.market_portfolio_autonomous_sentinel.AutonomousSentinel')
    def test_run_autonomous_sentinel_wrapper(self, mock_sentinel_cls):
        mock_instance = mock_sentinel_cls.return_value
        mock_instance.run_surveillance.return_value = True

        res = run_autonomous_sentinel(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            threshold=self.threshold
        )

        self.assertTrue(res)
        mock_sentinel_cls.assert_called_once_with(
            storage_file=self.storage_file,
            threshold=self.threshold
        )
        mock_instance.run_surveillance.assert_called_once_with(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

    def test_sentinel_stream_handling_with_bytes(self):
        garbage_bytes = uuid.uuid4().bytes + b"\xff\x00\xaa"
        stream_io = io.BytesIO(garbage_bytes)
        
        sentinel = AutonomousSentinel(
            storage_file=self.storage_file,
            threshold=self.threshold
        )
        
        with patch('skills.market_portfolio_autonomous_sentinel.MarketParser') as mock_parser_cls:
            mock_parser = mock_parser_cls.return_value
            mock_parser.fetch_price.return_value = 42.42
            
            with patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator') as mock_agg_cls:
                mock_agg = mock_agg_cls.return_value
                mock_agg.build_predictive_forecast.return_value = {
                    'forecast': 100.0,
                    'percentage_shift': 50.0
                }
                
                with patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts') as mock_dispatch:
                    res = sentinel.run_surveillance(
                        symbol=self.symbol,
                        url=self.url,
                        telegram_token=self.telegram_token,
                        chat_id=self.chat_id
                    )
                    self.assertTrue(res)
                    self.assertEqual(stream_io.read(), garbage_bytes)