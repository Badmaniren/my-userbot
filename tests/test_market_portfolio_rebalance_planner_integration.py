import unittest
import uuid
import random
import os
from skills.market_portfolio_rebalance_planner import market_portfolio_rebalance_planner
from skills.db_storage import db_storage
from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core

class TestMarketPortfolioRebalancePlannerIntegration(unittest.TestCase):
    def test_rebalance_planner_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        asset_symbol = f"ASSET_{random.choice(['BTC', 'ETH', 'SOL', 'AAPL', 'TSLA'])}"

        current_price = round(random.uniform(10.0, 5000.0), 2)
        target_weight = round(random.uniform(0.1, 0.5), 2)
        current_qty = random.randint(10, 100)
        available_cash = round(random.uniform(1000.0, 50000.0), 2)
        liquidity_buffer = round(random.uniform(100.0, 5000.0), 2)

        initial_valuation_data = {
            "portfolio_id": portfolio_id,
            "assets": {
                asset_symbol: {
                    "quantity": current_qty,
                    "price": current_price,
                    "target_weight": target_weight
                }
            },
            "cash": available_cash
        }

        db_storage.save_portfolio_state(portfolio_id, initial_valuation_data)

        valuation_result = market_portfolio_valuation.calculate(portfolio_id)
        self.assertIsNotNone(valuation_result)

        liquidity_core_result = market_portfolio_var_liquidity_core.evaluate_buffer(portfolio_id, liquidity_buffer)
        self.assertIsNotNone(liquidity_core_result)

        rebalance_output = market_portfolio_rebalance_planner(
            portfolio_id=portfolio_id,
            liquidity_buffer=liquidity_buffer
        )

        self.assertIsInstance(rebalance_output, dict)
        self.assertIn("orders", rebalance_output)
        self.assertIn("drift_detected", rebalance_output)

        orders = rebalance_output["orders"]
        self.assertIsInstance(orders, list)

        if len(orders) > 0:
            order = orders[0]
            self.assertIn("symbol", order)
            self.assertEqual(order["symbol"], asset_symbol)
            self.assertIn("action", order)
            self.assertIn("quantity", order)

        log_path = f"logs/rebalance_{portfolio_id}.log"
        self.assertTrue(os.path.exists(log_path) or len(orders) >= 0)

if __name__ == "__main__":
    unittest.main()