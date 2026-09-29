import unittest
import uuid
import random

from skills.market_portfolio_allocation_balancer import MarketPortfolioAllocationBalancer, balance_portfolio
from skills.db_storage import save_portfolio_state, get_portfolio_state
from skills.market_parser import fetch_latest_market_quotes
from skills.market_portfolio_slippage_model import calculate_slippage
from skills.market_portfolio_audit_log_exporter import export_audit_log


class TestMarketPortfolioAllocationBalancerIntegration(unittest.TestCase):

    def test_end_to_end_portfolio_balancing_and_storage(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        asset_symbol = f"ASSET_{uuid.uuid4().hex[:4].upper()}"

        initial_quantity = random.randint(50, 200)
        target_weight = round(random.uniform(0.1, 0.9), 2)

        initial_state = {
            asset_symbol: {
                "quantity": initial_quantity,
                "target_weight": target_weight
            }
        }

        save_portfolio_state(portfolio_id, initial_state)

        retrieved_state = get_portfolio_state(portfolio_id)
        self.assertIn(asset_symbol, retrieved_state)
        self.assertEqual(retrieved_state[asset_symbol]["quantity"], initial_quantity)

        quotes = fetch_latest_market_quotes([asset_symbol])
        self.assertIsInstance(quotes, (dict, list, type(None)))

        slippage = calculate_slippage(asset_symbol, initial_quantity)
        self.assertIsNotNone(slippage)

        balance_result = balance_portfolio(portfolio_id, quotes)
        self.assertEqual(balance_result.get("status"), "success")
        self.assertEqual(balance_result.get("portfolio_id"), portfolio_id)

        balancer = MarketPortfolioAllocationBalancer()
        current_price = round(random.uniform(10.0, 500.0), 2)
        liquidity = random.randint(5000, 50000)

        portfolio_data = {
            asset_symbol: {
                "target_weight": target_weight,
                "current_price": current_price,
                "liquidity": liquidity
            }
        }

        balanced_data = balancer.balance(portfolio_data)
        self.assertIn(asset_symbol, balanced_data)
        self.assertEqual(balanced_data[asset_symbol]["status"], "success")
        self.assertGreater(balanced_data[asset_symbol]["allocated_shares"], 0)

        audit_data = {
            "portfolio_id": portfolio_id,
            "asset": asset_symbol,
            "allocated_shares": balanced_data[asset_symbol]["allocated_shares"]
        }
        export_result = export_audit_log(audit_data)
        self.assertIsNotNone(export_result)


if __name__ == "__main__":
    unittest.main()