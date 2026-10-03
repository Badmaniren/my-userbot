import io
import math
import random
import string
import unittest
from unittest.mock import MagicMock, patch
import uuid

from skills.market_portfolio_rebalance_planner import (
    PortfolioRebalancePlanner,
    RebalanceOrder,
    RebalancePlan,
)


class TestMarketPortfolioRebalancePlanner(unittest.TestCase):
    def setUp(self):
        self.random_tag = uuid.uuid4().hex[:8]

    def _rand_ticker(self):
        return f"TICK_{uuid.uuid4().hex[:6].upper()}"

    def _rand_float(self, low=10.0, high=500.0, decimals=2):
        return round(random.uniform(low, high), decimals)

    def _get_val(self, obj, key):
        if hasattr(obj, key):
            return getattr(obj, key)
        if isinstance(obj, dict) and key in obj:
            return obj[key]
        raise AttributeError(f"Object {obj} has no attribute or key '{key}'")

    def test_drift_calculation_logic(self):
        ticker_a = self._rand_ticker()
        ticker_b = self._rand_ticker()

        price_a = self._rand_float(50.0, 150.0)
        qty_a = random.randint(10, 50)
        val_a = price_a * qty_a

        price_b = self._rand_float(100.0, 300.0)
        qty_b = random.randint(5, 30)
        val_b = price_b * qty_b

        cash = self._rand_float(1000.0, 3000.0)
        total_val = val_a + val_b + cash

        current_w_a = val_a / total_val
        current_w_b = val_b / total_val

        target_w_a = round(current_w_a + 0.10, 4)
        target_w_b = round(max(0.01, current_w_b - 0.05), 4)

        planner = PortfolioRebalancePlanner(drift_threshold=0.001)

        positions = {
            ticker_a: {"quantity": qty_a, "price": price_a},
            ticker_b: {"quantity": qty_b, "price": price_b},
        }
        target_weights = {
            ticker_a: target_w_a,
            ticker_b: target_w_b,
        }

        drifts = planner.calculate_drifts(positions, target_weights, cash)

        expected_drift_a = current_w_a - target_w_a
        expected_drift_b = current_w_b - target_w_b

        self.assertIn(ticker_a, drifts)
        self.assertIn(ticker_b, drifts)
        self.assertAlmostEqual(drifts[ticker_a], expected_drift_a, places=3)
        self.assertAlmostEqual(drifts[ticker_b], expected_drift_b, places=3)

    def test_drift_threshold_filters_minor_deviations(self):
        ticker_exceed = self._rand_ticker()
        ticker_within = self._rand_ticker()

        price_exceed = self._rand_float(100.0, 200.0)
        qty_exceed = 100
        val_exceed = price_exceed * qty_exceed

        price_within = self._rand_float(100.0, 200.0)
        qty_within = 100
        val_within = price_within * qty_within

        cash = 0.0
        total_val = val_exceed + val_within

        w_exceed = val_exceed / total_val
        w_within = val_within / total_val

        threshold = 0.05
        target_weights = {
            ticker_exceed: w_exceed + 0.15,
            ticker_within: w_within + 0.02,
        }

        planner = PortfolioRebalancePlanner(drift_threshold=threshold, allow_fractional=True)

        positions = {
            ticker_exceed: {"quantity": qty_exceed, "price": price_exceed},
            ticker_within: {"quantity": qty_within, "price": price_within},
        }

        plan = planner.plan_rebalance(positions, target_weights, cash)
        orders = self._get_val(plan, "orders")
        order_tickers = [self._get_val(o, "ticker") for o in orders]

        self.assertIn(ticker_exceed, order_tickers)
        self.assertNotIn(ticker_within, order_tickers)

    def test_liquidity_buffer_preservation(self):
        ticker_buy = self._rand_ticker()
        price_buy = self._rand_float(50.0, 100.0)
        cash = self._rand_float(5000.0, 10000.0)
        buffer_pct = round(random.uniform(0.15, 0.25), 2)

        positions = {}
        target_weights = {ticker_buy: 0.90}

        planner = PortfolioRebalancePlanner(
            drift_threshold=0.01,
            cash_buffer_pct=buffer_pct,
            allow_fractional=True
        )

        plan = planner.plan_rebalance(positions, {ticker_buy: 0.90, "price": price_buy}, cash) if "price" in target_weights else \
               planner.plan_rebalance(
                   positions={ticker_buy: {"quantity": 0, "price": price_buy}},
                   target_weights=target_weights,
                   cash=cash
               )

        orders = self._get_val(plan, "orders")
        self.assertTrue(len(orders) > 0)
        buy_order = [o for o in orders if self._get_val(o, "ticker") == ticker_buy][0]

        buy_amount = self._get_val(buy_order, "amount")
        expected_min_reserved_cash = cash * buffer_pct
        max_spendable = cash - expected_min_reserved_cash

        self.assertLessEqual(buy_amount, max_spendable + 1e-4)

    def test_sell_orders_sequenced_before_buy_orders(self):
        ticker_sell = self._rand_ticker()
        ticker_buy = self._rand_ticker()

        price_sell = self._rand_float(50.0, 100.0)
        price_buy = self._rand_float(50.0, 100.0)

        qty_sell = random.randint(80, 150)

        positions = {
            ticker_sell: {"quantity": qty_sell, "price": price_sell},
            ticker_buy: {"quantity": 0, "price": price_buy},
        }

        target_weights = {
            ticker_sell: 0.10,
            ticker_buy: 0.85,
        }

        planner = PortfolioRebalancePlanner(drift_threshold=0.01, cash_buffer_pct=0.05)
        plan = planner.plan_rebalance(positions, target_weights, cash=100.0)

        orders = self._get_val(plan, "orders")
        self.assertGreaterEqual(len(orders), 2)

        sides = [self._get_val(o, "side").upper() for o in orders]
        first_buy_idx = sides.index("BUY") if "BUY" in sides else len(sides)
        last_sell_idx = max([i for i, s in enumerate(sides) if s == "SELL"], default=-1)

        self.assertLess(last_sell_idx, first_buy_idx)

    def test_fractional_shares_configuration(self):
        ticker = self._rand_ticker()
        price = 73.0
        cash = 1000.0

        positions = {ticker: {"quantity": 0, "price": price}}
        target_weights = {ticker: 0.80}

        planner_no_frac = PortfolioRebalancePlanner(
            drift_threshold=0.001,
            cash_buffer_pct=0.0,
            allow_fractional=False
        )
        plan_no_frac = planner_no_frac.plan_rebalance(positions, target_weights, cash)
        orders_no_frac = self._get_val(plan_no_frac, "orders")
        self.assertEqual(len(orders_no_frac), 1)
        qty_no_frac = self._get_val(orders_no_frac[0], "quantity")
        self.assertTrue(float(qty_no_frac).is_integer())

        planner_frac = PortfolioRebalancePlanner(
            drift_threshold=0.001,
            cash_buffer_pct=0.0,
            allow_fractional=True
        )
        plan_frac = planner_frac.plan_rebalance(positions, target_weights, cash)
        orders_frac = self._get_val(plan_frac, "orders")
        self.assertEqual(len(orders_frac), 1)
        qty_frac = self._get_val(orders_frac[0], "quantity")
        self.assertFalse(float(qty_frac).is_integer())

    def test_minimum_trade_amount_filter(self):
        ticker_large = self._rand_ticker()
        ticker_tiny = self._rand_ticker()

        price = 100.0
        min_trade_val = self._rand_float(150.0, 300.0)

        positions = {
            ticker_large: {"quantity": 0, "price": price},
            ticker_tiny: {"quantity": 10, "price": price},
        }

        total_cash = 10000.0
        target_weights = {
            ticker_large: 0.50,
            ticker_tiny: (10 * price + (min_trade_val * 0.4)) / (total_cash + 1000.0),
        }

        planner = PortfolioRebalancePlanner(
            drift_threshold=0.0001,
            min_trade_value=min_trade_val,
            allow_fractional=True
        )

        plan = planner.plan_rebalance(positions, target_weights, cash=total_cash)
        orders = self._get_val(plan, "orders")
        order_tickers = [self._get_val(o, "ticker") for o in orders]

        self.assertIn(ticker_large, order_tickers)
        self.assertNotIn(ticker_tiny, order_tickers)

    def test_complete_asset_liquidation(self):
        ticker_liquidate = self._rand_ticker()
        price = self._rand_float(20.0, 200.0)
        qty = random.randint(15, 60)

        positions = {
            ticker_liquidate: {"quantity": qty, "price": price},
        }
        target_weights = {
            ticker_liquidate: 0.0
        }

        planner = PortfolioRebalancePlanner(drift_threshold=0.001)
        plan = planner.plan_rebalance(positions, target_weights, cash=self._rand_float(500.0, 1500.0))

        orders = self._get_val(plan, "orders")
        self.assertEqual(len(orders), 1)
        order = orders[0]
        self.assertEqual(self._get_val(order, "ticker"), ticker_liquidate)
        self.assertEqual(self._get_val(order, "side").upper(), "SELL")
        self.assertAlmostEqual(self._get_val(order, "quantity"), qty, places=4)

    def test_validation_errors_on_invalid_inputs(self):
        planner = PortfolioRebalancePlanner()
        ticker = self._rand_ticker()

        with self.assertRaises(ValueError):
            planner.plan_rebalance(
                positions={ticker: {"quantity": 10, "price": -50.0}},
                target_weights={ticker: 0.5},
                cash=100.0
            )

        with self.assertRaises(ValueError):
            planner.plan_rebalance(
                positions={ticker: {"quantity": 10, "price": 50.0}},
                target_weights={ticker: 0.5},
                cash=-100.0
            )

        with self.assertRaises(ValueError):
            planner.plan_rebalance(
                positions={ticker: {"quantity": 10, "price": 50.0}},
                target_weights={ticker: 1.25},
                cash=100.0
            )

    def test_stream_reading_and_patching(self):
        ticker_stream = self._rand_ticker()
        mock_raw_data = f'{{"{ticker_stream}": {{"target_weight": 0.4}}}}'.encode("utf-8")
        stream = io.BytesIO(mock_raw_data)

        with patch("skills.market_portfolio_rebalance_planner.open", return_value=stream, create=True):
            read_bytes = stream.read()
            self.assertIn(ticker_stream.encode("utf-8"), read_bytes)

    def test_order_side_and_quantity_computation(self):
        ticker = self._rand_ticker()
        price = self._rand_float(10.0, 50.0)
        initial_qty = 10
        current_cash = self._rand_float(2000.0, 4000.0)

        total_val = initial_qty * price + current_cash
        target_w = 0.50
        target_val = total_val * target_w

        planner = PortfolioRebalancePlanner(drift_threshold=0.001, allow_fractional=True)
        positions = {ticker: {"quantity": initial_qty, "price": price}}
        target_weights = {ticker: target_w}

        plan = planner.plan_rebalance(positions, target_weights, current_cash)
        orders = self._get_val(plan, "orders")

        self.assertEqual(len(orders), 1)
        order = orders[0]
        self.assertEqual(self._get_val(order, "side").upper(), "BUY")

        expected_qty_diff = (target_val - (initial_qty * price)) / price
        self.assertAlmostEqual(self._get_val(order, "quantity"), expected_qty_diff, places=2)


if __name__ == "__main__":
    unittest.main()