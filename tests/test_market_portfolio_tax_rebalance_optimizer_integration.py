import unittest
import uuid
import random
import os
from skills.market_portfolio_tax_rebalance_optimizer import market_portfolio_tax_rebalance_optimizer
from skills.db_storage import db_storage
from skills.market_portfolio_tax_calculator import market_portfolio_tax_calculator
from skills.market_portfolio_valuation import market_portfolio_valuation

class TestMarketPortfolioTaxRebalanceoptimizerIntegration(unittest.TestCase):
    def test_tax_rebalance_optimizer_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        asset_ticker = f"TICK_{random.choice(['AAPL', 'MSFT', 'GOOG', 'AMZN'])}"
        initial_shares = random.randint(10, 500)
        purchase_price = round(random.uniform(50.0, 300.0), 2)
        current_price = round(purchase_price * random.uniform(0.8, 1.5), 2)

        db_storage.save_portfolio_position({
            "portfolio_id": portfolio_id,
            "ticker": asset_ticker,
            "shares": initial_shares,
            "purchase_price": purchase_price
        })

        valuation_res = market_portfolio_valuation.calculate_value(portfolio_id)
        self.assertIsNotNone(valuation_res)

        tax_calc_res = market_portfolio_tax_calculator.evaluate_capital_gains(
            portfolio_id=portfolio_id,
            ticker=asset_ticker,
            current_price=current_price
        )
        self.assertIsNotNone(tax_calc_res)

        target_allocation = round(random.uniform(0.1, 0.5), 2)
        optimization_result = market_portfolio_tax_rebalance_optimizer.optimize(
            portfolio_id=portfolio_id,
            target_allocations={asset_ticker: target_allocation},
            tax_bracket=0.15
        )

        self.assertIsInstance(optimization_result, dict)
        self.assertIn("status", optimization_result)
        self.assertEqual(optimization_result.get("portfolio_id"), portfolio_id)

        report_path = f"reports/rebalance_{portfolio_id}.json"
        if os.path.exists(report_path):
            self.assertTrue(os.path.getsize(report_path) > 0)

if __name__ == "__main__":
    unittest.main()