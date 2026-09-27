import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_tax_rebalance_optimizer import (
    optimize_tax_rebalance,
    calculate_capital_gains,
    evaluate_portfolio_tax_liability
)


class TestMarketPortfolioTaxRebalanceOptimizer(unittest.TestCase):

    def setUp(self):
        self.rand_portfolio_id = uuid.uuid4().hex
        self.rand_asset_ticker = "".join(random.choices(string.ascii_uppercase, k=5))
        self.rand_shares = random.randint(10, 1000)
        self.rand_purchase_price = round(random.uniform(10.0, 500.0), 2)
        self.rand_current_price = round(random.uniform(10.0, 500.0), 2)
        self.rand_tax_rate = round(random.uniform(0.05, 0.35), 2)
        self.rand_dividend_yield = round(random.uniform(0.0, 0.1), 4)

    def test_calculate_capital_gains_positive(self):
        total_cost = self.rand_shares * self.rand_purchase_price
        current_value = self.rand_shares * self.rand_current_price
        expected_gain = current_value - total_cost

        asset_data = {
            "ticker": self.rand_asset_ticker,
            "shares": self.rand_shares,
            "purchase_price": self.rand_purchase_price,
            "current_price": self.rand_current_price
        }

        gain = calculate_capital_gains(asset_data)
        self.assertAlmostEqual(gain, expected_gain, places=2)

    def test_evaluate_portfolio_tax_liability_with_io(self):
        mock_payload = (
            f"portfolio_id:{self.rand_portfolio_id},"
            f"ticker:{self.rand_asset_ticker},"
            f"gain:{random.randint(1000, 50000)}"
        ).encode('utf-8')

        mock_stream = io.BytesIO(mock_payload)

        with patch('skills.market_portfolio_tax_rebalance_optimizer.db_storage') as mock_db:
            mock_db.fetch_stream.return_value = mock_stream

            result = evaluate_portfolio_tax_liability(self.rand_portfolio_id, self.rand_tax_rate)

            self.assertIn("tax_liability", result)
            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], self.rand_portfolio_id)
            self.assertGreaterEqual(result["tax_liability"], 0.0)

    def test_optimize_tax_rebalance_strategy(self):
        assets = [
            {
                "ticker": "".join(random.choices(string.ascii_uppercase, k=4)),
                "shares": random.randint(1, 100),
                "purchase_price": round(random.uniform(5.0, 100.0), 2),
                "current_price": round(random.uniform(5.0, 100.0), 2),
                "target_weight": round(random.uniform(0.1, 0.5), 2)
            }
            for _ in range(random.randint(2, 5))
        ]

        portfolio_config = {
            "portfolio_id": self.rand_portfolio_id,
            "tax_rate": self.rand_tax_rate,
            "assets": assets
        }

        with patch('skills.market_portfolio_tax_rebalance_optimizer.market_portfolio_strategy_optimizer') as mock_optimizer:
            mock_optimizer.calculate_target_weights.return_value = portfolio_config

            strategy = optimize_tax_rebalance(self.rand_portfolio_id, portfolio_config)

            self.assertIsInstance(strategy, dict)
            self.assertIn("recommended_actions", strategy)
            self.assertIn("estimated_tax_impact", strategy)
            self.assertEqual(strategy.get("portfolio_id"), self.rand_portfolio_id)

    def test_optimize_tax_rebalance_handles_empty_stream_gracefully(self):
        empty_stream = io.BytesIO(b"")

        with patch('skills.market_portfolio_tax_rebalance_optimizer.db_storage') as mock_db:
            mock_db.fetch_stream.return_value = empty_stream

            result = evaluate_portfolio_tax_liability(self.rand_portfolio_id, self.rand_tax_rate)

            self.assertIsNotNone(result)
            self.assertEqual(result.get("tax_liability"), 0.0)


if __name__ == "__main__":
    unittest.main()