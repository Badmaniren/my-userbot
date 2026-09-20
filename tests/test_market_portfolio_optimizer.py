import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
from skills.market_portfolio_optimizer import (
    PortfolioOptimizer,
    optimize_portfolio_weights,
    calculate_historical_volatility,
    calculate_expected_returns
)

class TestMarketPortfolioOptimizer(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol_a = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.symbol_b = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.symbols = [self.symbol_a, self.symbol_b]
        self.optimizer = PortfolioOptimizer(self.storage_file)

    def test_calculate_historical_volatility_random_data(self):
        mock_returns = [
            [random.uniform(-0.05, 0.05) for _ in range(10)],
            [random.uniform(-0.05, 0.05) for _ in range(10)]
        ]

        with patch.object(self.optimizer, 'load_returns_data', return_value=mock_returns):
            volatility = self.optimizer.calculate_volatility(self.symbols)
            self.assertIsInstance(volatility, dict)
            for sym in self.symbols:
                self.assertIn(sym, volatility)
                self.assertGreaterEqual(volatility[sym], 0.0)

    def test_calculate_expected_returns_dynamic(self):
        random_prices = [
            [random.randint(100, 500) for _ in range(15)],
            [random.randint(50, 300) for _ in range(15)]
        ]

        with patch.object(self.optimizer, 'fetch_historical_prices', return_value=random_prices):
            expected_returns = calculate_expected_returns(self.symbols, self.storage_file)
            self.assertIsInstance(expected_returns, dict)
            self.assertEqual(len(expected_returns), len(self.symbols))
            for sym in self.symbols:
                self.assertIn(sym, expected_returns)

    def test_optimize_portfolio_weights_allocation(self):
        expected_returns = {
            self.symbol_a: random.uniform(0.05, 0.20),
            self.symbol_b: random.uniform(0.05, 0.20)
        }
        volatilities = {
            self.symbol_a: random.uniform(0.10, 0.30),
            self.symbol_b: random.uniform(0.10, 0.30)
        }

        weights = optimize_portfolio_weights(expected_returns, volatilities)

        self.assertIsInstance(weights, dict)
        self.assertEqual(len(weights), 2)
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=4)
        for sym in self.symbols:
            self.assertIn(sym, weights)
            self.assertGreaterEqual(weights[sym], 0.0)
            self.assertLessEqual(weights[sym], 1.0)

    def test_optimizer_class_pipeline_integration(self):
        random_stream_dump = io.BytesIO(f'{uuid.uuid4().hex}:{random.uniform(1.0, 100.0)}'.encode('utf-8'))

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.return_value = random_stream_dump
            result_weights = self.optimizer.run_optimization_pipeline(self.symbols)

            self.assertIsInstance(result_weights, dict)
            self.assertTrue(all(isinstance(k, str) for k in result_weights.keys()))
            self.assertTrue(all(isinstance(v, float) for v in result_weights.values()))

    def test_calculate_historical_volatility_standalone(self):
        series = [random.uniform(-0.1, 0.1) for _ in range(25)]
        vol = calculate_historical_volatility(series)
        self.assertIsInstance(vol, float)
        self.assertGreaterEqual(vol, 0.0)

    def test_optimizer_empty_data_handling(self):
        with patch.object(self.optimizer, 'load_returns_data', return_value=[]):
            weights = self.optimizer.optimize([])
            self.assertEqual(weights, {})

if __name__ == '__main__':
    unittest.main()