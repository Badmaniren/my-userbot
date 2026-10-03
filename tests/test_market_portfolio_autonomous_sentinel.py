import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_portfolio_autonomous_sentinel import AutonomousSentinel, run_autonomous_sentinel

class TestAutonomousSentinel(unittest.TestCase):

    def setUp(self):
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/{''.join(random.choices(string.ascii_lowercase, k=4))}"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.threshold = round(random.uniform(1.0, 10.0), 2)

    def test_init_strict_types(self):
        sentinel = AutonomousSentinel(storage_file=self.storage_file, threshold=self.threshold)
        self.assertEqual(sentinel.storage_file, self.storage_file)
        self.assertEqual(sentinel.threshold, float(self.threshold))

        with self.assertRaises(ValueError):
            AutonomousSentinel(threshold='not_a_float')

    def test_run_surveillance_stable(self):
        sentinel = AutonomousSentinel(storage_file=self.storage_file, threshold=self.threshold)
        
        mock_price = round(random.uniform(50.0, 150.0), 2)
        mock_forecast = mock_price + round(random.uniform(0.0, self.threshold - 0.1), 2)
        mock_shift = round(((mock_forecast - mock_price) / mock_price) * 100, 2)
        if abs(mock_shift) >= self.threshold:
            mock_shift = self.threshold - 0.5

        with patch('skills.market_portfolio_autonomous_sentinel.MarketParser') as MockParserClass, \
             patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator') as MockAggregatorClass, \
             patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts') as mock_dispatch:
            
            parser_instance = MockParserClass.return_value
            parser_instance.fetch_price = MagicMock(return_value=mock_price)
            
            aggregator_instance = MockAggregatorClass.return_value
            aggregator_instance.build_predictive_forecast = MagicMock(return_value={
                'forecast': mock_forecast,
                'percentage_shift': mock_shift
            })

            result = sentinel.run_surveillance(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id
            )

            self.assertEqual(result["status"], "stable")
            self.assertFalse(bool(result))
            mock_dispatch.assert_not_called()

    def test_run_surveillance_triggered(self):
        sentinel = AutonomousSentinel(storage_file=self.storage_file, threshold=self.threshold)
        
        mock_price = round(random.uniform(50.0, 150.0), 2)
        mock_forecast = mock_price + round(random.uniform(self.threshold, self.threshold + 10.0), 2)
        mock_shift = self.threshold + round(random.uniform(1.0, 5.0), 2)

        with patch('skills.market_portfolio_autonomous_sentinel.MarketParser') as MockParserClass, \
             patch('skills.market_portfolio_autonomous_sentinel.PredictiveAggregator') as MockAggregatorClass, \
             patch('skills.market_portfolio_autonomous_sentinel.dispatch_portfolio_alerts') as mock_dispatch:
            
            parser_instance = MockParserClass.return_value
            parser_instance.fetch_price = MagicMock(return_value=mock_price)
            
            aggregator_instance = MockAggregatorClass.return_value
            aggregator_instance.build_predictive_forecast = MagicMock(return_value={
                'forecast': mock_forecast,
                'percentage_shift': mock_shift
            })

            result = sentinel.run_surveillance(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id
            )

            self.assertEqual(result["status"], "triggered")
            self.assertTrue(bool(result))
            mock_dispatch.assert_called_once()
            _, kwargs = mock_dispatch.call_args
            self.assertEqual(kwargs['telegram_token'], self.telegram_token)
            self.assertEqual(kwargs['chat_id'], self.chat_id)
            self.assertIn(self.symbol, kwargs['message'])

    def test_run_autonomous_sentinel_function(self):
        with patch('skills.market_portfolio_autonomous_sentinel.AutonomousSentinel') as MockSentinelClass:
            sentinel_instance = MockSentinelClass.return_value
            expected_result = {
                "status": random.choice(["stable", "triggered"]),
                "forecast": {'forecast': 100.0, 'percentage_shift': 0.0}
            }
            sentinel_instance.run_surveillance.return_value = expected_result

            res = run_autonomous_sentinel(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file,
                threshold=self.threshold
            )

            MockSentinelClass.assert_called_once_with(
                storage_file=self.storage_file,
                threshold=self.threshold
            )
            sentinel_instance.run_surveillance.assert_called_once_with(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id
            )
            self.assertEqual(res, expected_result)

if __name__ == '__main__':
    unittest.main()