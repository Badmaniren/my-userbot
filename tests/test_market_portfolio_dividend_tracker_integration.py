import unittest
import uuid
import random
import os
from skills import market_portfolio_dividend_tracker
from skills import market_portfolio_tax_calculator
from skills import db_storage

class RealTaxCalculator:
    def calculate_tax(self, amount, rate):
        return amount * (rate / 100.0)

class RealApiGateway:
    def __init__(self, dps):
        self.dps = dps
    def get_dividend_info(self, ticker):
        return {"dividend_per_share": self.dps}
    def pull_raw_stream(self, asset_id):
        pass

class RealDbStorage:
    def __init__(self, assets):
        self.assets = assets
    def get_portfolio_assets(self, portfolio_id):
        return self.assets

class TestDividendTrackerIntegration(unittest.TestCase):
    def test_end_to_end_dividend_workflow(self):
        portfolio_id = str(uuid.uuid4())
        asset_ticker = f"TICK_{random.randint(1000, 9999)}"
        shares_count = random.randint(10, 500)
        tax_rate = float(random.randint(5, 20))
        dps = round(random.uniform(1.0, 10.0), 2)
        
        tax_calc = RealTaxCalculator()
        api_gw = RealApiGateway(dps)
        
        assets_data = [{
            "ticker": asset_ticker,
            "shares": shares_count,
            "dividend_per_share": dps,
            "tax_rate": tax_rate
        }]
        db = RealDbStorage(assets_data)
        
        tracker = market_portfolio_dividend_tracker.DividendTracker(
            db_storage=db,
            tax_calculator=tax_calc,
            api_gateway=api_gw
        )
        
        projected = tracker.calculate_projected_dividends(asset_ticker, shares_count, tax_rate)
        
        self.assertEqual(projected["ticker"], asset_ticker)
        expected_gross = shares_count * dps
        expected_tax = expected_gross * (tax_rate / 100.0)
        expected_net = expected_gross - expected_tax
        
        self.assertAlmostEqual(projected["gross_dividend"], expected_gross)
        self.assertAlmostEqual(projected["tax_withheld"], expected_tax)
        self.assertAlmostEqual(projected["net_dividend"], expected_net)
        
        aggregated = tracker.aggregate_portfolio_dividends(portfolio_id)
        self.assertEqual(aggregated["portfolio_id"], portfolio_id)
        self.assertAlmostEqual(aggregated["total_net_dividends"], expected_net)
        
        amount_val = round(random.uniform(100.0, 5000.0), 2)
        processed = market_portfolio_dividend_tracker.process_dividends(portfolio_id, asset_ticker, amount_val)
        
        self.assertIn("dividend_id", processed)
        self.assertTrue(processed["dividend_id"].endswith(portfolio_id))
        self.assertEqual(processed["asset"], asset_ticker)
        self.assertEqual(processed["amount"], amount_val)
        
        test_file = f"export_{uuid.uuid4()}.txt"
        try:
            db_storage.export_to_file(portfolio_id, test_file)
            self.assertTrue(os.path.exists(test_file))
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

if __name__ == "__main__":
    unittest.main()