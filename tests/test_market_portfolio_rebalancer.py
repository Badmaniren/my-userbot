import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_rebalancer import MarketPortfolioRebalancer, market_portfolio_rebalancer

class TestMarketPortfolioRebalancer(unittest.TestCase):
    def setUp(self):
        self.rebalancer = MarketPortfolioRebalancer()
        self.asset_a = f"ASSET_{uuid.uuid4().hex[:6].upper()}"
        self.asset_b = f"ASSET_{uuid.uuid4().hex[:6].upper()}"

    def test_compute_rebalance_orders_zero_value(self):
        portfolio = {self.asset_a: 0.0, self.asset_b: 0.0}
        targets = {self.asset_a: 0.5, self.asset_b: 0.5}
        threshold = round(random.uniform(0.01, 0.05), 4)
        min_trade = round(random.uniform(10.0, 50.0), 2)

        result = self.rebalancer.compute_rebalance_orders(portfolio, targets, threshold, min_trade)
        self.assertEqual(result["orders"], [])
        self.assertEqual(result["deviations"], {self.asset_a: 0.0, self.asset_b: 0.0})

    def test_compute_rebalance_orders_buy_and_sell(self):
        portfolio = {self.asset_a: 800.0, self.asset_b: 200.0}
        targets = {self.asset_a: 0.5, self.asset_b: 0.5}
        threshold = 0.01
        min_trade = 10.0

        result = self.rebalancer.compute_rebalance_orders(portfolio, targets, threshold, min_trade)

        self.assertEqual(result["deviations"][self.asset_a], 0.3)
        self.assertEqual(result["deviations"][self.asset_b], -0.3)

        orders = result["orders"]
        self.assertEqual(len(orders), 2)

        actions = {o["asset"]: o["action"] for o in orders}
        self.assertEqual(actions[self.asset_a], "SELL")
        self.assertEqual(actions[self.asset_b], "BUY")

        amounts = {o["asset"]: o["amount"] for o in orders}
        self.assertAlmostEqual(amounts[self.asset_a], 300.0)
        self.assertAlmostEqual(amounts[self.asset_b], 300.0)

    def test_compute_rebalance_orders_below_threshold(self):
        portfolio = {self.asset_a: 502.0, self.asset_b: 498.0}
        targets = {self.asset_a: 0.5, self.asset_b: 0.5}
        threshold = 0.05
        min_trade = 1.0

        result = self.rebalancer.compute_rebalance_orders(portfolio, targets, threshold, min_trade)
        self.assertEqual(result["orders"], [])

    def test_compute_rebalance_orders_below_min_trade(self):
        portfolio = {self.asset_a: 504.0, self.asset_b: 496.0}
        targets = {self.asset_a: 0.5, self.asset_b: 0.5}
        threshold = 0.01
        min_trade = 100.0

        result = self.rebalancer.compute_rebalance_orders(portfolio, targets, threshold, min_trade)
        self.assertEqual(result["orders"], [])

    def test_process_market_stream(self):
        stream_payload = uuid.uuid4().hex
        mock_mp = MagicMock()
        expected_result = {"status": uuid.uuid4().hex}
        mock_mp.parse_stream.return_value = expected_result

        with patch("skills.market_portfolio_rebalancer.market_parser", mock_mp):
            res = self.rebalancer.process_market_stream(stream_payload)
            mock_mp.parse_stream.assert_called_once_with(stream_payload)
            self.assertEqual(res, expected_result)


class TestMarketPortfolioRebalancerIntegration(unittest.TestCase):
    def test_market_portfolio_rebalancer_wrapper_existing(self):
        portfolio_id = uuid.uuid4().hex
        symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        price = round(random.uniform(50.0, 150.0), 2)

        mock_db = MagicMock(return_value={
            "assets": {
                symbol: {
                    "quantity": 10,
                    "target_weight": 1.0
                }
            },
            "trigger_threshold": 0.01,
            "min_order_value": 5.0
        })

        with patch("skills.market_portfolio_rebalancer.db_storage", mock_db):
            config = {
                "portfolio_id": portfolio_id,
                "market_data": {
                    "symbol": symbol,
                    "price": price
                }
            }
            res = market_portfolio_rebalancer(config)
            self.assertIn("orders", res)
            self.assertIn("deviations", res)

    def test_market_portfolio_rebalancer_wrapper_default(self):
        portfolio_id = uuid.uuid4().hex
        symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"

        mock_db = MagicMock(return_value=None)

        with patch("skills.market_portfolio_rebalancer.db_storage", mock_db):
            config = {
                "portfolio_id": portfolio_id,
                "market_data": {
                    "symbol": symbol,
                    "price": 100.0
                }
            }
            res = market_portfolio_rebalancer(config)
            self.assertIn("orders", res)
            self.assertIn("deviations", res)
            self.assertIn(symbol, res["deviations"])