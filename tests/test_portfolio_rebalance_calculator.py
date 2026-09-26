import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.portfolio_rebalance_calculator import PortfolioRebalanceCalculator, calculate_portfolio_rebalance

class TestPortfolioRebalanceCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = PortfolioRebalanceCalculator()
        self.asset_id_1 = f"asset_{uuid.uuid4().hex[:6]}"
        self.asset_id_2 = f"asset_{uuid.uuid4().hex[:6]}"

    def test_compute_orders_buy(self):
        rand_total = random.randint(10000, 50000)
        rand_cash = random.randint(5000, 20000)
        portfolio_state = {
            "assets": {
                self.asset_id_1: {
                    "current_weight": 0.10,
                    "target_weight": 0.40,
                    "price": 100.0
                }
            },
            "cash": rand_cash,
            "total_value": rand_total,
            "drift_threshold": 0.05
        }
        orders = self.calculator.compute_orders(portfolio_state)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["asset_id"], self.asset_id_1)
        self.assertEqual(orders[0]["action"], "BUY")
        self.assertGreater(orders[0]["quantity"], 0)

    def test_compute_orders_sell(self):
        rand_total = random.randint(10000, 50000)
        rand_cash = random.randint(1000, 5000)
        portfolio_state = {
            "assets": {
                self.asset_id_2: {
                    "current_weight": 0.60,
                    "target_weight": 0.20,
                    "price": 50.0
                }
            },
            "cash": rand_cash,
            "total_value": rand_total,
            "drift_threshold": 0.05
        }
        orders = self.calculator.compute_orders(portfolio_state)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["asset_id"], self.asset_id_2)
        self.assertEqual(orders[0]["action"], "SELL")
        self.assertGreater(orders[0]["quantity"], 0)

    def test_compute_orders_within_threshold(self):
        rand_total = random.randint(10000, 50000)
        rand_cash = random.randint(1000, 5000)
        portfolio_state = {
            "assets": {
                self.asset_id_1: {
                    "current_weight": 0.25,
                    "target_weight": 0.27,
                    "price": 10.0
                }
            },
            "cash": rand_cash,
            "total_value": rand_total,
            "drift_threshold": 0.05
        }
        orders = self.calculator.compute_orders(portfolio_state)
        self.assertEqual(len(orders), 0)

    def test_compute_orders_limited_by_cash(self):
        portfolio_state = {
            "assets": {
                self.asset_id_1: {
                    "current_weight": 0.0,
                    "target_weight": 0.80,
                    "price": 100.0
                }
            },
            "cash": 250.0,
            "total_value": 1000.0,
            "drift_threshold": 0.05
        }
        orders = self.calculator.compute_orders(portfolio_state)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["action"], "BUY")
        self.assertEqual(orders[0]["quantity"], 2)

    def test_calculate_portfolio_rebalance_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        mock_portfolio_data = {
            "cash": 1000.0,
            "assets": {
                "AAPL": {"shares": 5, "target_weight": 0.5},
                "MSFT": {"shares": 2, "target_weight": 0.5}
            }
        }
        mock_prices = {"AAPL": 150.0, "MSFT": 300.0}

        with patch("skills.portfolio_rebalance_calculator.DatabaseStorage") as MockDb, \
             patch("skills.portfolio_rebalance_calculator.MarketParser") as MockParser, \
             patch("skills.portfolio_rebalance_calculator.PortfolioValuation") as MockValuation:

            db_instance = MockDb.return_value
            db_instance.get_portfolio_state.return_value = mock_portfolio_data

            parser_instance = MockParser.return_value
            parser_instance.fetch_latest_prices.return_value = mock_prices

            val_instance = MockValuation.return_value
            val_instance.calculate_total_value.return_value = 2350.0

            result = calculate_portfolio_rebalance(portfolio_id, drift_threshold=0.01)

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["status"], "success")
            self.assertIn("orders", result)
            db_instance.save_rebalance_orders.assert_called_once()

    def test_calculate_portfolio_rebalance_zero_valuation(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        mock_portfolio_data = {
            "cash": 500.0,
            "assets": {
                "BTC": {"shares": 1, "target_weight": 1.0}
            }
        }
        mock_prices = {"BTC": 10000.0}

        with patch("skills.portfolio_rebalance_calculator.DatabaseStorage") as MockDb, \
             patch("skills.portfolio_rebalance_calculator.MarketParser") as MockParser, \
             patch("skills.portfolio_rebalance_calculator.PortfolioValuation") as MockValuation:

            db_instance = MockDb.return_value
            db_instance.get_portfolio_state.return_value = mock_portfolio_data

            parser_instance = MockParser.return_value
            parser_instance.fetch_latest_prices.return_value = mock_prices

            val_instance = MockValuation.return_value
            val_instance.calculate_total_value.return_value = 0.0

            result = calculate_portfolio_rebalance(portfolio_id, drift_threshold=0.05)

            self.assertEqual(result["status"], "success")
            self.assertIsInstance(result["orders"], list)
            db_instance.save_rebalance_orders.assert_called_once()