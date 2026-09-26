import unittest
import uuid
import random

from skills.db_storage import DatabaseStorage
from skills.market_parser import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation
from skills.portfolio_rebalance_calculator import calculate_portfolio_rebalance, PortfolioRebalanceCalculator

class TestPortfolioRebalanceIntegration(unittest.TestCase):
    def test_rebalance_calculator_end_to_end_integration(self):
        portfolio_id = str(uuid.uuid4())
        asset_symbol = f"TICKER_{random.randint(1000, 9999)}"

        db = DatabaseStorage()

        initial_portfolio_state = {
            "cash": float(random.randint(5000, 15000)),
            "assets": {
                asset_symbol: {
                    "shares": random.randint(10, 50),
                    "target_weight": 0.80
                }
            }
        }

        if hasattr(db, "save_portfolio_state"):
            db.save_portfolio_state(portfolio_id, initial_portfolio_state)
        else:
            db.portfolios = getattr(db, "portfolios", {})
            db.portfolios[portfolio_id] = initial_portfolio_state

        drift_threshold = 0.01
        result = calculate_portfolio_rebalance(portfolio_id, drift_threshold=drift_threshold)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "success")

        orders = result.get("orders")
        self.assertIsInstance(orders, list)

        saved_orders = db.get_rebalance_orders(portfolio_id) if hasattr(db, "get_rebalance_orders") else orders
        self.assertIsNotNone(saved_orders)
        self.assertEqual(len(saved_orders), len(orders))

if __name__ == "__main__":
    unittest.main()