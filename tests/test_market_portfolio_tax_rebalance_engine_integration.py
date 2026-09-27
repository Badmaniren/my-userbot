import unittest
import uuid
import random
import os
from skills.market_portfolio_tax_rebalance_engine import market_portfolio_tax_rebalance_engine
from skills.market_portfolio_dividend_tracker import market_portfolio_dividend_tracker
from skills.market_portfolio_tax_calculator import market_portfolio_tax_calculator
from skills.db_storage import db_storage

class IntegrationTestMarketPortfolioTaxRebalanceEngine(unittest.TestCase):

    def test_rebalance_engine_integration_real_flow(self):
        portfolio_id = str(uuid.uuid4())
        asset_ticker = f"TICKER_{random.randint(1000, 9999)}"
        initial_shares = random.randint(10, 100)
        share_price = round(random.uniform(50.0, 500.0), 2)
        dividend_amount = round(random.uniform(1.0, 10.0), 2)
        tax_rate = round(random.uniform(0.1, 0.25), 2)

        dividend_data = {
            "portfolio_id": portfolio_id,
            "ticker": asset_ticker,
            "dividend_per_share": dividend_amount,
            "shares": initial_shares
        }
        div_result = market_portfolio_dividend_tracker(dividend_data)
        self.assertIsNotNone(div_result)

        tax_data = {
            "portfolio_id": portfolio_id,
            "income": initial_shares * dividend_amount,
            "tax_rate": tax_rate
        }
        tax_result = market_portfolio_tax_calculator(tax_data)
        self.assertIsNotNone(tax_result)

        rebalance_payload = {
            "portfolio_id": portfolio_id,
            "target_allocation": {asset_ticker: 1.0},
            "current_holdings": {asset_ticker: initial_shares},
            "current_prices": {asset_ticker: share_price},
            "include_dividends": True,
            "include_taxes": True
        }

        engine_result = market_portfolio_tax_rebalance_engine(rebalance_payload)
        self.assertIsInstance(engine_result, dict)
        self.assertIn("status", engine_result)
        self.assertEqual(engine_result.get("portfolio_id"), portfolio_id)

        db_check = db_storage({"action": "get_portfolio", "portfolio_id": portfolio_id})
        self.assertIsNotNone(db_check)

        output_file_path = f"rebalance_report_{portfolio_id}.json"
        self.assertTrue(os.path.exists(output_file_path) or "report_generated" in engine_result)

        if os.path.exists(output_file_path):
            os.remove(output_file_path)

if __name__ == "__main__":
    unittest.main()