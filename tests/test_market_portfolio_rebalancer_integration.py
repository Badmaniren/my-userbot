import unittest
import os
import uuid
import random
from skills.market_portfolio_rebalancer import MarketPortfolioRebalancer, market_portfolio_rebalancer

class TestMarketPortfolioRebalancerIntegration(unittest.TestCase):
    def test_rebalance_orders_computation_and_audit(self):
        portfolio_id = str(uuid.uuid4())
        drift_threshold = round(random.uniform(0.01, 0.05), 3)

        asset_name = f"ASSET_{uuid.uuid4().hex[:6]}"
        actual_weight = round(random.uniform(0.1, 0.3), 2)
        target_weight = round(actual_weight + drift_threshold + 0.05, 2)
        total_portfolio_value = round(random.uniform(10000.0, 50000.0), 2)

        portfolio_state = {
            asset_name: {
                "actual_weight": actual_weight,
                "target_weight": target_weight,
                "value": total_portfolio_value
            }
        }

        rebalancer = MarketPortfolioRebalancer()
        orders = rebalancer.compute_rebalance_orders(portfolio_state, drift_threshold)

        self.assertIsInstance(orders, list)
        self.assertGreaterEqual(len(orders), 1)

        found_order = False
        for order in orders:
            if order.get("asset") == asset_name:
                found_order = True
                self.assertEqual(order.get("action"), "BUY")
                expected_amount = abs(target_weight - actual_weight) * total_portfolio_value
                self.assertAlmostEqual(order.get("amount"), expected_amount, places=2)

        self.assertTrue(found_order)

        result = market_portfolio_rebalancer(portfolio_id, drift_threshold)

        self.assertIsInstance(result, dict)
        self.assertIn("orders", result)

        audit_path = f"audit_rebalance_{portfolio_id}.log"
        try:
            self.assertTrue(os.path.exists(audit_path))
            with open(audit_path, "r") as f:
                content = f.read()
                self.assertIn(portfolio_id, content)
                self.assertIn(str(drift_threshold), content)
        finally:
            if os.path.exists(audit_path):
                os.remove(audit_path)

if __name__ == "__main__":
    unittest.main()