import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json

from skills.market_portfolio_rebalancer import (
    PortfolioRebalancer,
    calculate_optimal_proportions,
    rebalance_portfolio
)

class TestMarketPortfolioRebalancer(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/market"
        self.random_target_alloc = {
            self.random_symbol: round(random.uniform(0.1, 0.9), 2),
            ''.join(random.choices(string.ascii_uppercase, k=4)): round(random.uniform(0.1, 0.9), 2)
        }

    def test_portfolio_rebalancer_initialization(self):
        rebalancer = PortfolioRebalancer(self.storage_file)
        self.assertEqual(rebalancer.storage_file, self.storage_file)

    def test_calculate_optimal_proportions_logic(self):
        portfolio_data = {
            uuid.uuid4().hex: round(random.uniform(100.0, 1000.0), 2),
            uuid.uuid4().hex: round(random.uniform(50.0, 500.0), 2)
        }
        total_val = sum(portfolio_data.values())

        proportions = calculate_optimal_proportions(portfolio_data)

        for asset, val in portfolio_data.items():
            expected_ratio = val / total_val
            self.assertAlmostEqual(proportions[asset], expected_ratio, places=4)

    def test_rebalance_portfolio_execution(self):
        mock_current_prices = {
            self.random_symbol: random.randint(10, 500)
        }

        with patch('skills.market_portfolio_rebalancer.PortfolioValuation') as MockValuation:
            instance = MockValuation.return_value
            instance.evaluate_portfolio.return_value = mock_current_prices

            rebalancer = PortfolioRebalancer(self.storage_file)
            result = rebalancer.rebalance(self.random_url, self.random_target_alloc)

            self.assertIsInstance(result, dict)
            self.assertTrue(len(result) > 0)

    def test_rebalance_portfolio_file_loading_error(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            rebalancer = PortfolioRebalancer(self.storage_file)
            data = rebalancer.load_data(self.storage_file)
            self.assertEqual(data, {})

    def test_rebalance_with_stream_mock(self):
        random_bytes = uuid.uuid4().bytes
        mock_file_stream = io.BytesIO(random_bytes)

        with patch('builtins.open', return_value=mock_file_stream):
            rebalancer = PortfolioRebalancer(self.storage_file)
            loaded = rebalancer.load_data(self.storage_file)
            self.assertIsInstance(loaded, dict)

    def test_rebalance_dispatch_calculations(self):
        asset_name = uuid.uuid4().hex
        current_amount = random.randint(1, 100)
        target_share = 0.5

        with patch.object(PortfolioRebalancer, 'load_data', return_value={asset_name: current_amount}):
            rebalancer = PortfolioRebalancer(self.storage_file)
            diff = rebalancer.calculate_difference(asset_name, target_share)
            self.assertIsInstance(diff, float)