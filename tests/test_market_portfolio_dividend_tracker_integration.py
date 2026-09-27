import unittest
import uuid
import random
import os
from skills import market_portfolio_dividend_tracker
from skills import market_portfolio_tax_calculator
from skills import db_storage

class IntegrationTestMarketPortfolioDividendTracker(unittest.TestCase):
    def test_dividend_tracker_integration_with_tax_calculator(self):
        test_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        test_asset_ticker = f"TICK_{random.randint(1000, 9999)}"
        random_dividend_amount = round(random.uniform(10.0, 5000.0), 2)
        random_tax_rate = round(random.uniform(0.09, 0.30), 2)

        db_storage.save_record(test_portfolio_id, {
            "asset": test_asset_ticker,
            "dividend": random_dividend_amount,
            "tax_rate": random_tax_rate
        })

        dividend_result = market_portfolio_dividend_tracker.process_dividends(
            portfolio_id=test_portfolio_id,
            asset=test_asset_ticker,
            amount=random_dividend_amount
        )

        self.assertIsNotNone(dividend_result)
        self.assertIn("dividend_id", dividend_result)

        tax_result = market_portfolio_tax_calculator.calculate_tax(
            portfolio_id=test_portfolio_id,
            dividend_data=dividend_result,
            rate=random_tax_rate
        )

        self.assertIsNotNone(tax_result)
        self.assertEqual(tax_result.get("portfolio_id"), test_portfolio_id)
        self.assertGreaterEqual(tax_result.get("net_amount", 0.0), 0.0)

        export_file_path = f"export_{uuid.uuid4().hex}.json"
        db_storage.export_to_file(test_portfolio_id, export_file_path)

        self.assertTrue(os.path.exists(export_file_path))
        
        if os.path.exists(export_file_path):
            os.remove(export_file_path)

if __name__ == "__main__":
    unittest.main()